# Nightly Network Account Maintenance

This script now supports mixed vendors in one nightly run:

- Aruba 6300 (`platform=aruba_6300`)
- Cisco 3700 (`platform=cisco_3700`)
- FortiGate firewalls (`platform=fortigate`)

For each device it will:

1. Change the admin account password.
2. Remove all local access users except `admin` (or `keep_users` overrides).
3. Optionally write the new password into Azure Key Vault.

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

Notes:

- `--mfa-client-id` defaults to Azure CLI public client ID. You can supply your own app registration client ID.
- Script sends an MFA claims challenge and validates token authentication method (`amr`) when available.
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
