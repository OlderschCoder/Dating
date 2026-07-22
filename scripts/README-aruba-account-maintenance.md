# Nightly Network Account Maintenance

This script now supports mixed vendors in one nightly run:

- Aruba 6300 (`platform=aruba_6300`)
- Cisco 3700 (`platform=cisco_3700`)
- FortiGate firewalls (`platform=fortigate`)

For each device it will:

1. Change the admin account password.
2. Remove all local access users except `admin` (or `keep_users` overrides).
3. Optionally write the new password into Azure Key Vault.

When discovery mode is used, each run can also update visibility for:

- new devices
- rogue/unknown devices
- platform changes versus baseline inventory

---

## 1) Install dependencies

```bash
python3 -m pip install -r scripts/requirements-aruba-maintenance.txt
```

---

## 2) Prepare inventory

Edit:

```text
scripts/network_devices.csv
```

Format:

```csv
host,platform,username,port,keep_users
10.0.10.11,aruba_6300,admin,22,admin
10.0.20.21,cisco_3700,admin,22,admin
10.0.30.31,fortigate,admin,22,admin
```

`keep_users` is comma-separated (e.g. `admin,svc_backup`).

---

## 2b) Auto-populate inventory by scanning your network

You now have two options:

### Option A: standalone discovery script (individual run)

If you run from a host inside your network, you can generate a starter inventory:

```bash
python3 scripts/discover_network_devices.py \
  --cidrs "10.0.10.0/24,10.0.20.0/24,10.0.30.0/24" \
  --output-csv scripts/network_devices.csv \
  --unknown-csv scripts/network_devices_unknown.csv \
  --username admin \
  --keep-users admin
```

### Option B: embedded discovery in maintenance run

This will discover first, then continue directly into password rotation/account cleanup:

```bash
python3 scripts/aruba_account_maintenance.py \
  --discover-cidrs "10.0.10.0/24,10.0.20.0/24,10.0.30.0/24" \
  --discover-output-csv scripts/network_devices.csv \
  --discover-unknown-csv scripts/network_devices_unknown.csv \
  --discover-baseline-csv scripts/network_devices.csv \
  --discover-delta-csv scripts/network_devices_delta.csv \
  --generate-new-password \
  --verbose
```

Optional SNMP-assisted fingerprinting (more accurate in either mode):

```bash
python3 scripts/discover_network_devices.py \
  --cidrs "10.0.10.0/24,10.0.20.0/24,10.0.30.0/24" \
  --snmp-community "<community>" \
  --baseline-csv scripts/network_devices.csv \
  --delta-csv scripts/network_devices_delta.csv \
  --output-csv scripts/network_devices.csv \
  --unknown-csv scripts/network_devices_unknown.csv
```

What it does:

- probes likely live hosts on TCP 22/443 by default
- fingerprints devices as `aruba_6300`, `cisco_3700`, or `fortigate` where possible
- writes unrecognized hosts to `network_devices_unknown.csv` for manual review
- can write `network_devices_delta.csv` (when baseline is provided) with statuses:
  - `NEW_SUPPORTED`
  - `NEW_ROGUE_UNKNOWN`
  - `ROGUE_UNKNOWN`
  - `PLATFORM_CHANGED`
  - `MISSING_FROM_SCAN`

---

## 3) Provide passwords

You can pass passwords using CLI args, env vars, or Azure Key Vault.

Environment variable option:

```bash
export NETWORK_CURRENT_PASSWORD='current_password_here'
export NETWORK_NEW_ADMIN_PASSWORD='new_password_here'
```

---

## 4) Dry-run first

```bash
python3 scripts/aruba_account_maintenance.py \
  --inventory-file scripts/network_devices.csv \
  --dry-run --verbose
```

---

## 5) Run for real

```bash
python3 scripts/aruba_account_maintenance.py \
  --inventory-file scripts/network_devices.csv \
  --verbose
```

---

## Azure Key Vault integration

If `--key-vault-url` is provided:

- current password can be read from `--current-password-secret-name`
- new password can be written to `--new-password-secret-name` after a successful run

Example:

```bash
python3 scripts/aruba_account_maintenance.py \
  --inventory-file scripts/network_devices.csv \
  --generate-new-password \
  --key-vault-url "https://YOURVAULT.vault.azure.net/" \
  --current-password-secret-name "network-admin-password" \
  --new-password-secret-name "network-admin-password" \
  --verbose
```

By default, Key Vault update is skipped if any device fails.
Use `--write-on-partial-success` to override.

---

## Forced MFA (phone or laptop biometrics)

Use `--require-mfa` to block execution until a user completes Microsoft Entra MFA.

### Phone-based MFA (device code flow)

Best for headless servers/terminals where the user approves sign-in on phone:

```bash
python3 scripts/aruba_account_maintenance.py \
  --inventory-file scripts/network_devices.csv \
  --require-mfa \
  --mfa-method phone \
  --mfa-auth-flow device_code \
  --mfa-tenant-id "<tenant-guid>" \
  --mfa-login-hint "admin@company.com" \
  --verbose
```

### Laptop biometric MFA (browser flow)

Best when using Windows Hello / passkey / platform biometric prompt in browser:

```bash
python3 scripts/aruba_account_maintenance.py \
  --inventory-file scripts/network_devices.csv \
  --require-mfa \
  --mfa-method biometric \
  --mfa-auth-flow browser \
  --mfa-tenant-id "<tenant-guid>" \
  --mfa-login-hint "admin@company.com" \
  --verbose
```

### Optional hardware security key (FIDO2)

Use this mode if you want sign-in to require a FIDO2 hardware key (for example, a Cryptnox-compatible key configured in Microsoft Entra):

```bash
python3 scripts/aruba_account_maintenance.py \
  --inventory-file scripts/network_devices.csv \
  --require-mfa \
  --mfa-method security_key \
  --mfa-auth-flow browser \
  --mfa-tenant-id "<tenant-guid>" \
  --mfa-login-hint "admin@company.com" \
  --verbose
```

Notes:

- `--mfa-client-id` defaults to Azure CLI public client ID. You can supply your own app registration client ID.
- Script sends an MFA claims challenge and validates token authentication method (`amr`) when available.
- Hardware key enforcement depends on your Entra authentication methods and Conditional Access policies.
- For strict enterprise enforcement, configure Conditional Access authentication strengths in Entra.

---

## Nightly cron example (2:00 AM)

Store non-secret runtime values in cron command; keep secrets in Key Vault:

```cron
0 2 * * * /usr/bin/python3 /workspace/scripts/aruba_account_maintenance.py --inventory-file /workspace/scripts/network_devices.csv --generate-new-password --key-vault-url https://YOURVAULT.vault.azure.net/ --current-password-secret-name network-admin-password --new-password-secret-name network-admin-password >> /var/log/network_account_maintenance.log 2>&1
```

If not using Key Vault, source env vars from a locked-down file first:

```cron
0 2 * * * . /etc/network/account-maintenance.env && /usr/bin/python3 /workspace/scripts/aruba_account_maintenance.py --inventory-file /workspace/scripts/network_devices.csv >> /var/log/network_account_maintenance.log 2>&1
```

Important:

- Human MFA (`--require-mfa`) is interactive and usually not suitable for unattended nightly cron.
- For unattended nightly runs, use managed identity/service principal to access Key Vault and enforce policy in Entra Conditional Access.

---

## Supporting policy and training docs

- `scripts/ADMIN-SOP-fido2.md`
- `scripts/HELPDESK-PLAYBOOK-fido2.md`
- `scripts/USER-STEP-BY-STEP-CONFIGURATION.md`
- `scripts/EXECUTIVE-CISO-BRIEF-network-admin-auth-and-rotation.md`
- `scripts/DOCUMENTATION-STANDARD.md`
