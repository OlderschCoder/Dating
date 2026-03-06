#!/usr/bin/env python3
"""
Nightly Aruba switch account maintenance.

Actions per switch:
1) Change admin password.
2) Remove all local users except those explicitly kept (default: admin).

Designed for Aruba AOS-CX defaults, but command templates are configurable
for other Aruba platforms.
"""

from __future__ import annotations

import argparse
import getpass
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set

try:
    from netmiko import ConnectHandler
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "Missing dependency: netmiko. Install with: pip install netmiko"
    ) from exc


DEFAULT_USER_REGEX = r"^([A-Za-z0-9_.-]+)\s+"
HEADER_TOKENS = {"username", "user", "name"}


@dataclass
class SwitchResult:
    ip: str
    success: bool
    removed_users: List[str]
    error: str = ""


def build_logger(log_file: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("aruba-account-maintenance")
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


def parse_ips(ips_file: Path) -> List[str]:
    ips: List[str] = []
    for line in ips_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ips.append(stripped)
    return ips


def parse_usernames(raw_output: str, user_regex: str) -> Set[str]:
    pattern = re.compile(user_regex, flags=re.MULTILINE)
    usernames: Set[str] = set()
    for match in pattern.finditer(raw_output):
        username = match.group(1).strip()
        if not username:
            continue
        if username.lower() in HEADER_TOKENS:
            continue
        usernames.add(username)
    return usernames


def resolve_secret(
    cli_value: str | None,
    env_var: str,
    prompt: str,
    *,
    allow_empty: bool = False,
) -> str:
    if cli_value:
        return cli_value

    env_value = os.getenv(env_var)
    if env_value:
        return env_value

    if not sys.stdin.isatty():
        raise ValueError(
            f"Secret was not provided via --{prompt.lower().replace(' ', '-')} "
            f"or {env_var} in non-interactive mode."
        )

    entered = getpass.getpass(f"{prompt}: ")
    if entered or allow_empty:
        return entered
    raise ValueError(f"{prompt} cannot be empty.")


def build_config_commands(
    *,
    new_admin_password: str,
    set_admin_password_command: str,
    delete_user_command: str,
    users_to_remove: Iterable[str],
) -> List[str]:
    commands = [set_admin_password_command.format(password=new_admin_password)]
    for username in sorted(users_to_remove, key=str.lower):
        commands.append(delete_user_command.format(username=username))
    return commands


def maintain_switch(
    *,
    ip: str,
    username: str,
    password: str,
    device_type: str,
    port: int,
    timeout: int,
    command_timeout: int,
    keep_users: Set[str],
    new_admin_password: str,
    show_users_command: str,
    user_regex: str,
    set_admin_password_command: str,
    delete_user_command: str,
    save_command: str,
    dry_run: bool,
    logger: logging.Logger,
) -> SwitchResult:
    logger.info("[%s] Connecting", ip)
    try:
        connection = ConnectHandler(
            device_type=device_type,
            host=ip,
            username=username,
            password=password,
            port=port,
            timeout=timeout,
        )
        with connection:
            raw_users = connection.send_command(
                show_users_command,
                read_timeout=command_timeout,
            )
            usernames = parse_usernames(raw_users, user_regex)
            users_to_remove = [
                user for user in usernames if user.lower() not in keep_users
            ]

            commands = build_config_commands(
                new_admin_password=new_admin_password,
                set_admin_password_command=set_admin_password_command,
                delete_user_command=delete_user_command,
                users_to_remove=users_to_remove,
            )

            if dry_run:
                logger.info("[%s] DRY-RUN commands: %s", ip, commands)
            else:
                logger.info(
                    "[%s] Applying changes (remove %d user(s))",
                    ip,
                    len(users_to_remove),
                )
                connection.send_config_set(commands, cmd_verify=False)
                if save_command:
                    connection.send_command_timing(save_command)

            return SwitchResult(
                ip=ip,
                success=True,
                removed_users=sorted(users_to_remove, key=str.lower),
            )
    except Exception as exc:  # broad on purpose: network auth and CLI errors
        logger.exception("[%s] Failed: %s", ip, exc)
        return SwitchResult(ip=ip, success=False, removed_users=[], error=str(exc))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Change Aruba admin password and remove local users except admin."
        )
    )
    parser.add_argument("--ips-file", required=True, help="Text file with switch IPs")
    parser.add_argument("--device-type", default="aruba_aoscx")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--current-password")
    parser.add_argument("--new-admin-password")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--command-timeout", type=int, default=30)
    parser.add_argument("--keep-users", default="admin")
    parser.add_argument("--show-users-command", default="show user")
    parser.add_argument("--user-regex", default=DEFAULT_USER_REGEX)
    parser.add_argument(
        "--set-admin-password-command",
        default='user admin password plaintext "{password}"',
    )
    parser.add_argument("--delete-user-command", default="no user {username}")
    parser.add_argument("--save-command", default="write memory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--log-file",
        default="aruba_account_maintenance.log",
        help="Log file path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = build_logger(Path(args.log_file), args.verbose)

    ips_file = Path(args.ips_file)
    if not ips_file.exists():
        logger.error("IP list file not found: %s", ips_file)
        return 2

    keep_users = {item.strip().lower() for item in args.keep_users.split(",") if item}
    if "admin" not in keep_users:
        # Requirement says keep only admin by default, so force it for safety.
        keep_users.add("admin")

    try:
        current_password = resolve_secret(
            args.current_password,
            "ARUBA_CURRENT_PASSWORD",
            "Current switch login password",
        )
        new_admin_password = resolve_secret(
            args.new_admin_password,
            "ARUBA_NEW_ADMIN_PASSWORD",
            "New admin password",
        )
    except ValueError as exc:
        logger.error(str(exc))
        return 2

    ips = parse_ips(ips_file)
    if not ips:
        logger.error("No switch IPs found in %s", ips_file)
        return 2

    results: List[SwitchResult] = []
    for ip in ips:
        result = maintain_switch(
            ip=ip,
            username=args.username,
            password=current_password,
            device_type=args.device_type,
            port=args.port,
            timeout=args.timeout,
            command_timeout=args.command_timeout,
            keep_users=keep_users,
            new_admin_password=new_admin_password,
            show_users_command=args.show_users_command,
            user_regex=args.user_regex,
            set_admin_password_command=args.set_admin_password_command,
            delete_user_command=args.delete_user_command,
            save_command=args.save_command,
            dry_run=args.dry_run,
            logger=logger,
        )
        results.append(result)

    failed = [res for res in results if not res.success]
    succeeded = [res for res in results if res.success]

    logger.info("Finished. Success: %d, Failed: %d", len(succeeded), len(failed))
    for res in succeeded:
        logger.info("[%s] Removed users: %s", res.ip, ", ".join(res.removed_users) or "none")
    for res in failed:
        logger.error("[%s] Error: %s", res.ip, res.error)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
