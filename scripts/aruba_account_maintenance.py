#!/usr/bin/env python3
"""
Nightly network account maintenance for:
- Aruba 6300 switches (AOS-CX)
- Cisco 3700 switches (IOS)
- FortiGate firewalls

Actions per device:
1) Change admin account password.
2) Remove all local access accounts except kept users (admin by default).
3) Optionally write the new password to Azure Key Vault.
"""

from __future__ import annotations

import argparse
import csv
import getpass
import io
import json
import logging
import os
import re
import secrets
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

try:
    from netmiko import ConnectHandler
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: netmiko. Install with: pip install netmiko"
    ) from exc

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    AZURE_LIBS_AVAILABLE = True
except ImportError:
    AZURE_LIBS_AVAILABLE = False

try:
    from msal import PublicClientApplication

    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False


HEADER_TOKENS = {"username", "user", "name"}
ENV_CURRENT_PASSWORD = "NETWORK_CURRENT_PASSWORD"
ENV_NEW_PASSWORD = "NETWORK_NEW_ADMIN_PASSWORD"
DEFAULT_MFA_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"


@dataclass(frozen=True)
class PlatformProfile:
    name: str
    netmiko_device_type: str
    show_users_command: str
    user_regex: str
    delete_user_command: str
    save_command: str
    apply_style: str  # "config_set" or "timing"


PLATFORM_PROFILES: Dict[str, PlatformProfile] = {
    "aruba_6300": PlatformProfile(
        name="aruba_6300",
        netmiko_device_type="aruba_aoscx",
        show_users_command="show user",
        user_regex=r"^([A-Za-z0-9_.-]+)\s+",
        delete_user_command="no user {username}",
        save_command="write memory",
        apply_style="config_set",
    ),
    "cisco_3700": PlatformProfile(
        name="cisco_3700",
        netmiko_device_type="cisco_ios",
        show_users_command="show running-config | include ^username",
        user_regex=r"^username\s+([A-Za-z0-9_.-]+)\b",
        delete_user_command="no username {username}",
        save_command="write memory",
        apply_style="config_set",
    ),
    "fortigate": PlatformProfile(
        name="fortigate",
        netmiko_device_type="fortinet",
        show_users_command="show system admin",
        user_regex=r'^\s*edit\s+"?([^"\s]+)"?',
        delete_user_command='delete "{username}"',
        save_command="",
        apply_style="timing",
    ),
}


@dataclass
class DeviceTarget:
    host: str
    platform: str
    username: str
    port: int
    keep_users: Set[str]


@dataclass
class DeviceResult:
    host: str
    platform: str
    success: bool
    removed_users: List[str]
    error: str = ""


@dataclass
class MfaConfig:
    required_method: str
    auth_flow: str
    tenant_id: str
    client_id: str
    login_hint: str
    scopes: List[str]


class AzureKeyVaultStore:
    def __init__(self, vault_url: str) -> None:
        if not AZURE_LIBS_AVAILABLE:
            raise RuntimeError(
                "Azure Key Vault libraries are not installed. "
                "Install azure-identity and azure-keyvault-secrets."
            )
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self._client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(self, name: str) -> str:
        return self._client.get_secret(name).value

    def set_secret(self, name: str, value: str) -> None:
        self._client.set_secret(name, value)


def build_mfa_claims_challenge(required_method: str) -> str:
    claims_values = {
        "any": ["mfa"],
        "phone": ["sms", "otp", "phone"],
        "biometric": ["fido", "fido2", "windowshello", "face", "fingerprint"],
        "security_key": ["fido", "fido2"],
    }
    payload = {
        "id_token": {
            "amr": {
                "essential": True,
                "values": claims_values[required_method],
            }
        }
    }
    return json.dumps(payload)


def normalize_amr_claims(id_token_claims: Dict[str, Any]) -> Set[str]:
    raw_amr = id_token_claims.get("amr")
    if isinstance(raw_amr, str):
        return {raw_amr.strip().lower()} if raw_amr.strip() else set()
    if isinstance(raw_amr, list):
        return {
            str(item).strip().lower()
            for item in raw_amr
            if str(item).strip()
        }
    return set()


def mfa_method_satisfied(required_method: str, amr_values: Set[str]) -> bool:
    if not amr_values:
        return False
    if required_method == "any":
        return bool(amr_values.intersection({"mfa", "otp", "sms", "phone", "fido", "fido2"}))
    if required_method == "phone":
        return bool(amr_values.intersection({"sms", "otp", "phone", "mfa"}))
    if required_method == "biometric":
        return bool(
            amr_values.intersection(
                {"fido", "fido2", "windowshello", "face", "fingerprint", "biometric"}
            )
        )
    if required_method == "security_key":
        return bool(amr_values.intersection({"fido", "fido2"}))
    return False


def enforce_mfa_or_raise(mfa_config: MfaConfig, logger: logging.Logger) -> None:
    if not MSAL_AVAILABLE:
        raise RuntimeError("Missing dependency: msal. Install with: pip install msal")

    authority = f"https://login.microsoftonline.com/{mfa_config.tenant_id}"
    app = PublicClientApplication(
        client_id=mfa_config.client_id,
        authority=authority,
    )
    claims_challenge = build_mfa_claims_challenge(mfa_config.required_method)

    logger.info(
        "MFA required (%s via %s flow). Waiting for interactive sign-in.",
        mfa_config.required_method,
        mfa_config.auth_flow,
    )

    if mfa_config.auth_flow == "device_code":
        flow = app.initiate_device_flow(
            scopes=mfa_config.scopes,
            claims_challenge=claims_challenge,
        )
        if "user_code" not in flow:
            raise RuntimeError(
                f"Failed to start device-code flow: {flow.get('error_description', flow)}"
            )
        logger.info(flow.get("message", "Complete the device code sign-in prompt."))
        result = app.acquire_token_by_device_flow(flow)
    else:
        result = app.acquire_token_interactive(
            scopes=mfa_config.scopes,
            login_hint=mfa_config.login_hint or None,
            prompt="select_account",
            claims_challenge=claims_challenge,
        )

    if "error" in result:
        raise RuntimeError(
            f"MFA authentication failed: {result.get('error_description', result['error'])}"
        )

    id_token_claims = result.get("id_token_claims") or {}
    amr_values = normalize_amr_claims(id_token_claims)
    if amr_values and not mfa_method_satisfied(mfa_config.required_method, amr_values):
        raise RuntimeError(
            "MFA was completed but not with an allowed method. "
            f"Required='{mfa_config.required_method}', token amr={sorted(amr_values)}"
        )

    if amr_values:
        logger.info("MFA satisfied via amr=%s", sorted(amr_values))
    else:
        logger.warning(
            "MFA login succeeded but token did not expose amr claim. "
            "Relying on tenant claims challenge enforcement."
        )


def build_logger(log_file: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("network-account-maintenance")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_keep_users(raw_value: str, admin_account: str) -> Set[str]:
    keep_users = {
        token.strip().lower()
        for token in raw_value.split(",")
        if token.strip()
    }
    keep_users.add(admin_account.lower())
    return keep_users


def parse_scopes(raw_value: str) -> List[str]:
    scopes = [token.strip() for token in raw_value.split(",") if token.strip()]
    if "openid" not in scopes:
        scopes.append("openid")
    if "profile" not in scopes:
        scopes.append("profile")
    return scopes


def parse_inventory_csv(
    inventory_file: Path,
    default_username: str,
    default_port: int,
    default_keep_users: Set[str],
    admin_account: str,
) -> List[DeviceTarget]:
    raw_lines = inventory_file.read_text(encoding="utf-8").splitlines()
    filtered_lines = [
        line
        for line in raw_lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not filtered_lines:
        return []

    reader = csv.DictReader(io.StringIO("\n".join(filtered_lines)))
    targets: List[DeviceTarget] = []
    for row in reader:
        host = (row.get("host") or "").strip()
        platform = (row.get("platform") or "").strip().lower()
        if not host or not platform:
            continue

        username = (row.get("username") or "").strip() or default_username
        port_str = (row.get("port") or "").strip()
        keep_raw = (row.get("keep_users") or "").strip()
        keep_users = (
            parse_keep_users(keep_raw, admin_account)
            if keep_raw
            else set(default_keep_users)
        )

        port = int(port_str) if port_str else default_port
        targets.append(
            DeviceTarget(
                host=host,
                platform=platform,
                username=username,
                port=port,
                keep_users=keep_users,
            )
        )
    return targets


def parse_ips_file(
    ips_file: Path,
    platform: str,
    username: str,
    port: int,
    keep_users: Set[str],
) -> List[DeviceTarget]:
    targets: List[DeviceTarget] = []
    for line in ips_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        targets.append(
            DeviceTarget(
                host=stripped,
                platform=platform,
                username=username,
                port=port,
                keep_users=set(keep_users),
            )
        )
    return targets


def parse_usernames(raw_output: str, user_regex: str) -> Set[str]:
    pattern = re.compile(user_regex, flags=re.MULTILINE)
    usernames: Set[str] = set()
    for match in pattern.finditer(raw_output):
        username = match.group(1).strip().strip('"')
        if not username:
            continue
        if username.lower() in HEADER_TOKENS:
            continue
        usernames.add(username)
    return usernames


def resolve_secret(
    *,
    cli_value: Optional[str],
    env_var: str,
    keyvault: Optional[AzureKeyVaultStore],
    keyvault_secret_name: Optional[str],
    prompt: str,
) -> str:
    if cli_value:
        return cli_value

    env_value = os.getenv(env_var)
    if env_value:
        return env_value

    if keyvault and keyvault_secret_name:
        return keyvault.get_secret(keyvault_secret_name)

    if not sys.stdin.isatty():
        raise ValueError(
            f"{prompt} not provided. Set CLI arg, {env_var}, or Key Vault secret."
        )

    entered = getpass.getpass(f"{prompt}: ")
    if entered:
        return entered
    raise ValueError(f"{prompt} cannot be empty.")


def generate_password(length: int) -> str:
    if length < 16:
        raise ValueError("Generated password length must be >= 16.")
    alphabet = string.ascii_letters + string.digits + "_-@#%!"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def build_config_commands(
    profile: PlatformProfile,
    admin_account: str,
    new_password: str,
    users_to_remove: Sequence[str],
) -> List[str]:
    if profile.name == "aruba_6300":
        commands = [f'user {admin_account} password plaintext "{new_password}"']
        commands.extend(
            profile.delete_user_command.format(username=username)
            for username in sorted(users_to_remove, key=str.lower)
        )
        return commands

    if profile.name == "cisco_3700":
        commands = [f"username {admin_account} privilege 15 secret 0 {new_password}"]
        commands.extend(
            profile.delete_user_command.format(username=username)
            for username in sorted(users_to_remove, key=str.lower)
        )
        return commands

    if profile.name == "fortigate":
        commands = [
            "config system admin",
            f'edit "{admin_account}"',
            f"set password {new_password}",
            "next",
        ]
        commands.extend(
            profile.delete_user_command.format(username=username)
            for username in sorted(users_to_remove, key=str.lower)
        )
        commands.append("end")
        return commands

    raise ValueError(f"Unsupported platform profile: {profile.name}")


def redact_commands(commands: Sequence[str], new_password: str) -> List[str]:
    return [command.replace(new_password, "***REDACTED***") for command in commands]


def apply_commands(connection: object, profile: PlatformProfile, commands: Sequence[str]) -> None:
    if profile.apply_style == "config_set":
        connection.send_config_set(list(commands), cmd_verify=False)
        return

    if profile.apply_style == "timing":
        for command in commands:
            connection.send_command_timing(
                command,
                strip_prompt=False,
                strip_command=False,
            )
        return

    raise ValueError(f"Unknown apply_style: {profile.apply_style}")


def maintain_device(
    *,
    target: DeviceTarget,
    current_password: str,
    new_password: str,
    admin_account: str,
    timeout: int,
    command_timeout: int,
    dry_run: bool,
    logger: logging.Logger,
) -> DeviceResult:
    profile = PLATFORM_PROFILES.get(target.platform)
    if not profile:
        return DeviceResult(
            host=target.host,
            platform=target.platform,
            success=False,
            removed_users=[],
            error=f"Unsupported platform '{target.platform}'",
        )

    logger.info("[%s][%s] Connecting", target.host, target.platform)
    try:
        connection = ConnectHandler(
            device_type=profile.netmiko_device_type,
            host=target.host,
            username=target.username,
            password=current_password,
            port=target.port,
            timeout=timeout,
            fast_cli=False,
        )
        with connection:
            raw_users = connection.send_command(
                profile.show_users_command,
                read_timeout=command_timeout,
            )
            usernames = parse_usernames(raw_users, profile.user_regex)
            users_to_remove = [
                user for user in usernames if user.lower() not in target.keep_users
            ]
            commands = build_config_commands(
                profile=profile,
                admin_account=admin_account,
                new_password=new_password,
                users_to_remove=users_to_remove,
            )

            if dry_run:
                logger.info(
                    "[%s][%s] DRY-RUN commands: %s",
                    target.host,
                    target.platform,
                    redact_commands(commands, new_password),
                )
            else:
                logger.info(
                    "[%s][%s] Applying changes (remove %d user(s))",
                    target.host,
                    target.platform,
                    len(users_to_remove),
                )
                apply_commands(connection, profile, commands)
                if profile.save_command:
                    connection.send_command_timing(profile.save_command)

            return DeviceResult(
                host=target.host,
                platform=target.platform,
                success=True,
                removed_users=sorted(users_to_remove, key=str.lower),
            )
    except Exception as exc:  # broad on purpose: network auth and CLI errors
        logger.exception("[%s][%s] Failed: %s", target.host, target.platform, exc)
        return DeviceResult(
            host=target.host,
            platform=target.platform,
            success=False,
            removed_users=[],
            error=str(exc),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Nightly password rotation + account cleanup for Aruba 6300, "
            "Cisco 3700, and FortiGate."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--inventory-file",
        help=(
            "CSV with columns: host,platform,username,port,keep_users. "
            "platform must be aruba_6300, cisco_3700, or fortigate."
        ),
    )
    source_group.add_argument(
        "--ips-file",
        help="Legacy mode: text file with one host per line.",
    )

    parser.add_argument(
        "--platform",
        choices=sorted(PLATFORM_PROFILES.keys()),
        default="aruba_6300",
        help="Used only with --ips-file legacy mode.",
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--admin-account", default="admin")
    parser.add_argument("--current-password")
    parser.add_argument("--new-admin-password")
    parser.add_argument("--generate-new-password", action="store_true")
    parser.add_argument("--generated-password-length", type=int, default=24)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--command-timeout", type=int, default=30)
    parser.add_argument("--keep-users", default="admin")

    parser.add_argument("--key-vault-url")
    parser.add_argument(
        "--current-password-secret-name",
        default="network-admin-password",
        help="Key Vault secret to read current password from if needed.",
    )
    parser.add_argument(
        "--new-password-secret-name",
        default="network-admin-password",
        help="Key Vault secret to write new password into.",
    )
    parser.add_argument(
        "--write-on-partial-success",
        action="store_true",
        help="Write new password to Key Vault even if some devices fail.",
    )
    parser.add_argument(
        "--require-mfa",
        action="store_true",
        help="Require interactive MFA sign-in before making any device changes.",
    )
    parser.add_argument(
        "--mfa-method",
        choices=["any", "phone", "biometric", "security_key"],
        default="any",
        help=(
            "Allowed MFA method type to enforce. "
            "Use security_key for FIDO2 hardware keys."
        ),
    )
    parser.add_argument(
        "--mfa-auth-flow",
        choices=["browser", "device_code"],
        default="browser",
        help="Use browser or device-code flow for MFA prompt.",
    )
    parser.add_argument(
        "--mfa-tenant-id",
        default=os.getenv("AZURE_TENANT_ID", ""),
        help="Microsoft Entra tenant ID used for MFA sign-in.",
    )
    parser.add_argument(
        "--mfa-client-id",
        default=os.getenv("MFA_CLIENT_ID", DEFAULT_MFA_CLIENT_ID),
        help=(
            "Public client application ID used for interactive MFA. "
            "Defaults to Azure CLI client ID unless MFA_CLIENT_ID is set."
        ),
    )
    parser.add_argument(
        "--mfa-login-hint",
        default=os.getenv("MFA_LOGIN_HINT", ""),
        help="Optional user principal (email) to prefill MFA sign-in.",
    )
    parser.add_argument(
        "--mfa-scopes",
        default="openid,profile,offline_access",
        help="Comma-separated scopes for MFA sign-in token request.",
    )

    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--log-file",
        default="network_account_maintenance.log",
        help="Log file path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = build_logger(Path(args.log_file), args.verbose)

    default_keep_users = parse_keep_users(args.keep_users, args.admin_account)

    keyvault: Optional[AzureKeyVaultStore] = None
    if args.key_vault_url:
        try:
            keyvault = AzureKeyVaultStore(args.key_vault_url)
            logger.info("Azure Key Vault enabled: %s", args.key_vault_url)
        except Exception as exc:
            logger.error("Unable to initialize Azure Key Vault client: %s", exc)
            return 2

    if args.require_mfa:
        if not args.mfa_tenant_id:
            logger.error("--mfa-tenant-id is required when --require-mfa is enabled.")
            return 2
        mfa_config = MfaConfig(
            required_method=args.mfa_method,
            auth_flow=args.mfa_auth_flow,
            tenant_id=args.mfa_tenant_id,
            client_id=args.mfa_client_id,
            login_hint=args.mfa_login_hint,
            scopes=parse_scopes(args.mfa_scopes),
        )
        try:
            enforce_mfa_or_raise(mfa_config, logger)
        except Exception as exc:
            logger.error("MFA enforcement failed: %s", exc)
            return 2

    try:
        current_password = resolve_secret(
            cli_value=args.current_password,
            env_var=ENV_CURRENT_PASSWORD,
            keyvault=keyvault,
            keyvault_secret_name=args.current_password_secret_name,
            prompt="Current device login password",
        )
    except ValueError as exc:
        logger.error(str(exc))
        return 2

    if args.new_admin_password:
        new_password = args.new_admin_password
    elif os.getenv(ENV_NEW_PASSWORD):
        new_password = os.getenv(ENV_NEW_PASSWORD) or ""
    elif args.generate_new_password:
        try:
            new_password = generate_password(args.generated_password_length)
        except ValueError as exc:
            logger.error(str(exc))
            return 2
        logger.info("Generated a new admin password for this run.")
    else:
        if not sys.stdin.isatty():
            logger.error(
                "New password not provided. Use --new-admin-password, "
                f"{ENV_NEW_PASSWORD}, or --generate-new-password."
            )
            return 2
        new_password = getpass.getpass("New admin password: ")
        if not new_password:
            logger.error("New admin password cannot be empty.")
            return 2

    if args.inventory_file:
        inventory_file = Path(args.inventory_file)
        if not inventory_file.exists():
            logger.error("Inventory file not found: %s", inventory_file)
            return 2
        targets = parse_inventory_csv(
            inventory_file=inventory_file,
            default_username=args.username,
            default_port=args.port,
            default_keep_users=default_keep_users,
            admin_account=args.admin_account,
        )
    else:
        ips_file = Path(args.ips_file)
        if not ips_file.exists():
            logger.error("IP list file not found: %s", ips_file)
            return 2
        targets = parse_ips_file(
            ips_file=ips_file,
            platform=args.platform,
            username=args.username,
            port=args.port,
            keep_users=default_keep_users,
        )

    if not targets:
        logger.error("No devices found to process.")
        return 2

    unsupported_platforms = sorted(
        {target.platform for target in targets if target.platform not in PLATFORM_PROFILES}
    )
    if unsupported_platforms:
        logger.error("Unsupported platform(s) in inventory: %s", unsupported_platforms)
        return 2

    logger.info("Processing %d device(s)", len(targets))
    results: List[DeviceResult] = []
    for target in targets:
        result = maintain_device(
            target=target,
            current_password=current_password,
            new_password=new_password,
            admin_account=args.admin_account,
            timeout=args.timeout,
            command_timeout=args.command_timeout,
            dry_run=args.dry_run,
            logger=logger,
        )
        results.append(result)

    failed = [res for res in results if not res.success]
    succeeded = [res for res in results if res.success]

    logger.info("Finished. Success: %d, Failed: %d", len(succeeded), len(failed))
    for res in succeeded:
        logger.info(
            "[%s][%s] Removed users: %s",
            res.host,
            res.platform,
            ", ".join(res.removed_users) or "none",
        )
    for res in failed:
        logger.error("[%s][%s] Error: %s", res.host, res.platform, res.error)

    if keyvault and not args.dry_run:
        should_write = not failed or args.write_on_partial_success
        if should_write:
            try:
                keyvault.set_secret(args.new_password_secret_name, new_password)
                logger.info(
                    "Updated Key Vault secret '%s' with new password.",
                    args.new_password_secret_name,
                )
            except Exception as exc:
                logger.error("Failed to write password to Key Vault: %s", exc)
                return 1
        else:
            logger.warning(
                "Skipped Key Vault update because some devices failed. "
                "Use --write-on-partial-success to override."
            )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
