# Executive + CISO Brief: Network Admin Access Hardening and Credential Rotation

## Audience

- Executive leadership (CIO/CISO/VP Infrastructure)
- Security architecture and engineering teams
- Network operations leadership

---

## 1) Executive Summary (non-technical)

This solution automates high-risk network administration controls across Aruba 6300 switches, Cisco 3700 switches, and FortiGate firewalls.

It provides four primary outcomes:

1. **Automated credential hygiene**  
   Nightly (or scheduled) admin password rotation across supported network devices.
2. **Privileged account reduction**  
   Removes local access accounts other than approved admins (default: `admin` only).
3. **Stronger identity controls**  
   Supports enforced MFA methods (phone, biometric, FIDO2 security key) for attended runs and integrates with Entra Conditional Access strategy.
4. **Continuous network visibility update**  
   Each discovery-enabled run can identify newly seen devices, rogue/unknown devices, and platform changes against baseline inventory.

The program reduces credential exposure windows, limits standing privileged access, and creates a repeatable control that is auditable.

---

## 2) What this solution does

### Core capability

The main automation (`aruba_account_maintenance.py`) performs, per device:

1. Connect to device over SSH.
2. Enumerate local admin/user accounts.
3. Change the admin account password.
4. Remove unauthorized local access accounts.
5. Save device configuration (platform-specific behavior).
6. Optionally write the new password into Azure Key Vault.

### Supported platforms

- Aruba 6300 (`aruba_6300`)
- Cisco 3700 (`cisco_3700`)
- FortiGate (`fortigate`)

### Inventory modes

- **Manual inventory file** (`--inventory-file`)
- **Legacy IP list** (`--ips-file`)
- **Embedded discovery mode** (`--discover-cidrs`) to discover devices and then immediately apply maintenance
- **Standalone discovery script** (`discover_network_devices.py`) to generate inventory separately

### Identity and MFA controls

- Optional enforced interactive MFA gate before device changes (`--require-mfa`)
- Allowed methods: `phone`, `biometric`, `security_key` (FIDO2 hardware key), or `any`
- Key Vault integration for secret read/write and centralized credential custody

---

## 3) How it works (technical overview)

### Workflow sequence

1. **Input source selected**
   - Inventory file, IP file, or CIDR-based discovery.
2. **(Optional) discovery phase**
   - Scans provided subnets for live hosts.
   - Fingerprints likely vendor/platform by SSH banner, HTTPS response title, and optional SNMP `sysDescr`.
    - Produces:
      - supported inventory CSV
      - unknown hosts CSV for review
      - optional delta CSV (new, rogue, changed, and missing-vs-baseline statuses)
3. **(Optional) MFA enforcement**
   - Interactive authentication via Microsoft identity platform.
   - Claims challenge requests required auth method.
4. **Credential sourcing**
   - Current password from CLI, environment variable, or Key Vault.
   - New password from CLI, env, or generated at runtime.
5. **Per-device maintenance execution**
   - Vendor-specific command sets are issued.
   - Non-approved local accounts are removed.
6. **Post-run control**
   - Results logged (success/failure per host).
   - New password optionally written to Key Vault.

### Platform-specific command behavior

- **Aruba 6300**: updates local admin password, removes users via Aruba command model.
- **Cisco 3700**: updates local admin secret, removes `username` entries.
- **FortiGate**: updates `config system admin`, deletes non-approved admins in relevant context.

### Control data produced

- Run log (`network_account_maintenance.log` by default)
- Device processing status summary
- Unknown-device review file (during discovery)
- Optional delta report (`network_devices_delta.csv`) for change/rogue/new device analysis

This provides operational evidence for audits and security reviews.

---

## 4) Security value / advantages

## A. Material risk reduction

- **Shortens credential exposure window** from potentially months to scheduled cadence.
- **Reduces lateral movement opportunities** by removing excess local admin accounts.
- **Improves privileged identity assurance** by integrating with phishing-resistant MFA pathways.

## B. Operational and governance benefits

- Repeatable control that does not rely on manual per-device changes.
- Centralized secret handling through Key Vault support.
- Inventory discovery can bootstrap brownfield environments quickly.
- Produces artifacts useful for audit, control validation, and incident response.

## C. Architecture flexibility

- Can run attended (with forced MFA) or unattended (service identity + policy controls).
- Supports multiple inventory and onboarding patterns for heterogeneous networks.

---

## 5) Limitations / disadvantages / risks

## A. Technical limitations

1. **Vendor command variability**
   - Firmware or platform CLI differences can require command profile adjustment.
2. **Fingerprinting confidence**
   - Discovery heuristics may classify some hosts as unknown and require human review.
3. **Interactive MFA for unattended jobs**
   - Forced human MFA mode is not suitable for fully unattended nightly cron.

## B. Operational risks

1. **Blast radius if misconfigured**
   - Incorrect keep-users policy or inventory errors could remove intended local accounts.
2. **Credential synchronization timing**
   - If password rotation succeeds on devices but Key Vault write fails, secret state can diverge.
3. **Dependency on network reachability**
   - Management network outages can cause partial execution outcomes.

## C. Governance and process gaps (if not addressed)

- No approval workflow by default before execution.
- No native ticket integration by default.
- No built-in dual-control for emergency overrides unless layered through process.

---

## 6) Recommended guardrails (CISO controls)

1. **Pilot first, then staged rollout** by network segment.
2. **Use break-glass accounts with monitoring**, excluded from strict automation where required.
3. **Mandatory dry-run for any logic changes** before production execution.
4. **Write-block behavior on partial success** unless explicitly approved (`--write-on-partial-success` governance).
5. **Change-control linkage** (run only with approved change ticket window).
6. **SIEM forwarding** for run logs and failure events.
7. **Quarterly control validation**:
   - unauthorized local accounts removed
   - password age policy evidence
   - MFA policy enforcement evidence in Entra

---

## 7) Strategic tradeoff: attended vs unattended operations

## Attended (forced MFA)

**Pros**
- Highest operator assurance at runtime
- Strong non-repudiation for privileged execution

**Cons**
- Not ideal for nightly fully unattended operations
- Human availability dependency

## Unattended (service identity + Key Vault + Conditional Access governance)

**Pros**
- Reliable nightly automation
- Predictable operational continuity

**Cons**
- Requires strong identity hardening for the automation identity
- Requires compensating controls (monitoring, PAM governance, least privilege)

---

## 8) Suggested KPI / KRI set for executive reporting

### KPI (performance)

- % of in-scope devices rotated within SLA window
- % of devices with only approved local admin accounts
- Mean time to remediate failed rotation targets

### KRI (risk)

- Count of unknown or unclassified devices in discovery output
- Count of failed runs writing to Key Vault
- Count of privileged runs outside approved change windows

---

## 9) Bottom line for leadership

This solution materially improves privileged network access control maturity by combining:

- identity hardening,
- password lifecycle automation,
- and local account minimization.

Its benefits are significant, but security outcomes depend on disciplined rollout, policy guardrails, and operational governance around exceptions and break-glass access.

