# Aruba Nightly Account Maintenance

This script connects to each Aruba switch in an IP list, changes the admin password, and removes all local users except `admin` (or any additional accounts listed in `--keep-users`).

## 1) Install dependency

```bash
python3 -m pip install -r scripts/requirements-aruba-maintenance.txt
```

## 2) Prepare switch list

Edit:

```text
scripts/aruba_switch_ips.txt
```

One switch IP or hostname per line.

## 3) Set secrets

Use environment variables so passwords are not stored in command history:

```bash
export ARUBA_CURRENT_PASSWORD='current_password_here'
export ARUBA_NEW_ADMIN_PASSWORD='new_password_here'
```

## 4) Test with dry-run first

```bash
python3 scripts/aruba_account_maintenance.py \
  --ips-file scripts/aruba_switch_ips.txt \
  --dry-run --verbose
```

## 5) Run for real

```bash
python3 scripts/aruba_account_maintenance.py \
  --ips-file scripts/aruba_switch_ips.txt \
  --verbose
```

## Nightly cron example (2:00 AM)

1. Save secrets in a root-only file, for example:

```bash
sudo mkdir -p /etc/aruba
sudo chmod 700 /etc/aruba
sudo sh -c "printf '%s\n' \
'ARUBA_CURRENT_PASSWORD=your_current_password' \
'ARUBA_NEW_ADMIN_PASSWORD=your_new_password' \
> /etc/aruba/account-maintenance.env"
sudo chmod 600 /etc/aruba/account-maintenance.env
```

2. Add a cron entry:

```bash
sudo crontab -e
```

```cron
0 2 * * * . /etc/aruba/account-maintenance.env && /usr/bin/python3 /workspace/scripts/aruba_account_maintenance.py --ips-file /workspace/scripts/aruba_switch_ips.txt >> /var/log/aruba_account_maintenance.log 2>&1
```

## Notes

- Defaults target Aruba AOS-CX (`--device-type aruba_aoscx`).
- If your Aruba model uses different CLI commands, override:
  - `--show-users-command`
  - `--set-admin-password-command`
  - `--delete-user-command`
  - `--save-command`
- Always run `--dry-run` first after changing command templates.
