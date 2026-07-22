# PAMSight Sentinel: Issues, Risks, Exploits, and Mitigations

## Purpose

This document explains how PAMSight Sentinel addresses security issues affecting privileged access to network devices.

The terms below are used deliberately:

- **Resolved**: the implemented control can remove the identified condition when it completes successfully.
- **Mitigated**: likelihood or impact is reduced, but residual risk remains.
- **Detected**: the condition is reported for investigation; it is not automatically contained.
- **Not covered**: a separate security control is required.

PAMSight Sentinel is not a replacement for vulnerability management, network access control (NAC), endpoint detection and response (EDR), or a full enterprise PAM platform.

---

## Executive risk summary

| Risk area | Control provided | Treatment |
|---|---|---|
| Stale or unauthorized local admin accounts | Enumerates and removes accounts outside the approved keep list | Resolved per successfully processed device |
| Long-lived shared admin passwords | Scheduled password generation and rotation | Mitigated |
| Password exposure outside a vault | Azure Key Vault read/write support | Mitigated |
| Phishing of privileged operators | Optional FIDO2/security-key MFA gate for attended runs | Mitigated |
| Unknown network equipment | CIDR discovery and unknown-device report | Detected |
| New or rogue equipment | Baseline comparison and delta status report | Detected |
| Device identity/platform drift | `PLATFORM_CHANGED` reporting | Detected |
| Missing managed devices | `MISSING_FROM_SCAN` reporting | Detected |
| Inconsistent manual administration | Repeatable vendor-specific automation | Mitigated |
| Device software vulnerabilities/exploits | No patch or CVE assessment capability | Not covered |

---

## Detailed issue and exploit-path matrix

| Issue or exploit path | Potential business impact | PAMSight Sentinel control | Treatment | Evidence produced | Residual risk / required control |
|---|---|---|---|---|---|
| Former employee or contractor account remains on a device | Unauthorized configuration changes, outage, data interception | Removes local accounts not listed in `keep_users` | Resolved after successful run | Per-device removed-user log | Central AAA accounts and vendor-specific hidden accounts require separate review |
| Attacker creates a persistent local admin account | Continued privileged access after initial compromise | Removes unapproved accounts on scheduled runs | Mitigated | Removed-user log | Attacker may recreate account; forward logs to SIEM and investigate root cause |
| Admin password is reused or remains unchanged for months | Credential stuffing and broad compromise | Generates and rotates a strong password on schedule | Mitigated | Run result and Key Vault secret version | Rotation does not protect an actively compromised session |
| Password is stored in scripts or shell history | Credential disclosure | Supports Azure Key Vault and environment-based secret sourcing | Mitigated | Key Vault audit/version history | CLI password arguments remain possible and should be prohibited operationally |
| Admin is phished for a password or OTP | Privileged account takeover | Optional FIDO2 hardware-key authentication for attended execution | Mitigated | Entra sign-in and Conditional Access logs | Strict enforcement must be configured in Entra; script claims alone are insufficient |
| Unauthorized device is connected to a managed subnet | Attack platform, interception, unmanaged access path | Discovery reports `NEW_ROGUE_UNKNOWN` or `ROGUE_UNKNOWN` | Detected | Delta and unknown-device CSV files | No automatic isolation; NAC/firewall/SOC response is required |
| New supported switch/firewall appears without onboarding | Unmanaged credentials and configuration drift | Discovery reports `NEW_SUPPORTED` | Detected | Delta CSV | Requires approval and controlled addition to baseline before maintenance |
| Device platform changes at an existing IP | Possible replacement, spoofing, or inventory error | Reports `PLATFORM_CHANGED` | Detected | Delta CSV | Validate asset identity, serial number, certificate, and change ticket |
| Known device disappears from scan | Outage, address change, segmentation issue, or evasion | Reports `MISSING_FROM_SCAN` | Detected | Delta CSV | A scan failure does not prove removal; confirm through monitoring/CMDB |
| Manual password changes differ across devices | Lockout and inconsistent operational state | Standardized vendor command profiles and centralized run | Mitigated | Success/failure summary | Firmware differences can still cause partial failure |
| Password changes on some devices but not others | Split credentials and operational lockout | Per-device failure reporting; Key Vault update is withheld by default on partial failure | Mitigated | Failure log and skipped-vault-update warning | Requires reconciliation procedure and potentially per-device secrets |
| Malicious or accidental inventory alteration | Changes applied to unintended devices | Explicit inventory source, platform validation, dry-run capability | Mitigated | Inventory CSV and dry-run logs | Add source control review, signed inventory, and change approval |
| Compromise of automation host | Theft of current/new credentials and mass device control | Key Vault support and MFA options reduce exposed secrets | Mitigated | Host, Entra, and Key Vault logs | Harden host, use managed identity, restrict egress, use least privilege, deploy EDR |
| SNMP community disclosure | Unauthorized network information access | SNMP is optional and used only for discovery | Partially mitigated | Scan configuration/logging | SNMPv2c is plaintext; prefer SNMPv3 or remove SNMP-assisted discovery |
| Device has known firmware CVE or exploitable service | Remote code execution, authentication bypass, denial of service | None | Not covered | None | Use authenticated vulnerability scanning, vendor advisories, and patch management |
| Rogue device must be blocked immediately | Active threat remains connected | Discovery only | Not covered | Rogue/unknown report | Integrate with NAC/SOAR/firewall quarantine after human-approved validation |
| Privileged session commands require recording | Audit gap and insider-risk exposure | Basic run logs only | Not covered | Automation log | Use enterprise PAM session proxy/recording and command authorization |
| Central RADIUS/TACACS+/Entra account governance | Orphaned central identities | Local account handling only | Not covered | None | Integrate IAM lifecycle, TACACS+/RADIUS, access reviews, and role governance |

---

## Common attack scenarios and control response

### Scenario 1: Stolen network-admin password

1. An attacker obtains the current local admin password.
2. Scheduled rotation shortens the period in which the password remains useful.
3. Key Vault reduces uncontrolled storage of the replacement password.
4. FIDO2 protects attended access to the maintenance workflow.

**Result:** likelihood and exposure duration are reduced.  
**Residual risk:** an active session, device backdoor, or compromised automation identity may remain.

### Scenario 2: Rogue firewall or switch appears

1. A new device begins responding on a scanned subnet.
2. Discovery fingerprints the device where possible.
3. Baseline comparison reports `NEW_SUPPORTED` or `NEW_ROGUE_UNKNOWN`.
4. Operations/SOC validates the device against the CMDB and change records.

**Result:** the previously unseen device becomes visible.  
**Residual risk:** PAMSight Sentinel does not automatically disconnect or quarantine it.

### Scenario 3: Attacker adds a hidden persistence account

1. The attacker creates an additional local admin account.
2. The next successful maintenance run enumerates local users.
3. The account is removed if it is not on the approved keep list.
4. The deletion is recorded in the run log.

**Result:** the unauthorized local account is removed.  
**Residual risk:** account recreation indicates ongoing compromise and requires incident response.

### Scenario 4: Partial password rotation

1. Some devices are unreachable or reject the command.
2. Successful and failed targets are separately reported.
3. The shared Key Vault secret is not updated by default when any target fails.

**Result:** silent partial completion is avoided.  
**Residual risk:** successfully changed devices may still hold the new password while failed devices retain the old password. Operators must reconcile the split state.

---

## Required companion controls

For production use, combine PAMSight Sentinel with:

1. Microsoft Entra Conditional Access and phishing-resistant authentication strength.
2. Azure Key Vault RBAC, managed identity, logging, and secret recovery controls.
3. TACACS+/RADIUS or another centralized network AAA service.
4. NAC for rogue-device containment.
5. SIEM/SOAR ingestion and alerting for discovery deltas and failed runs.
6. Vulnerability scanning and vendor firmware patch management.
7. Hardened privileged access workstations and automation hosts.
8. CMDB ownership and authorized-device baseline approval.
9. Enterprise PAM session recording where required.

---

## Recommended risk acceptance criteria

Production rollout should proceed only when:

- all target models and firmware versions pass dry-run and lab validation;
- break-glass access is tested and monitored;
- Key Vault access uses least privilege;
- failure and split-password reconciliation procedures are approved;
- rogue-device reports have an assigned SOC/NOC response owner;
- discovery scan scope is authorized;
- logs are retained and forwarded to the SIEM.

---

## Control effectiveness metrics

- Percentage of devices with only approved local accounts
- Password rotation success rate by platform
- Number and age of unresolved `NEW_ROGUE_UNKNOWN` findings
- Number of `PLATFORM_CHANGED` findings without approved change tickets
- Mean time to reconcile partial rotation failures
- Percentage of privileged attended runs using phishing-resistant MFA
- Number of devices missing from scan for more than one run

