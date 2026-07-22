# Admin SOP: Enforce FIDO2 for Privileged Accounts

This SOP enforces phishing-resistant authentication for administrator accounts in Microsoft Entra and Microsoft 365, with optional on-prem AD smart card enforcement.

## Scope

- In scope: all privileged cloud admin roles and designated admin user accounts.
- Out of scope: non-admin users (handled in separate rollout).

## Prerequisites

1. Two break-glass cloud admin accounts created and tested.
2. Break-glass accounts excluded from enforcement policies.
3. Cryptnox (or approved) FIDO2 keys procured and inventoried.
4. Pilot group created (`SG-Admins-FIDO2-Pilot`).
5. Enforced group created (`SG-Admins-FIDO2-Enforced`).

## Procedure

### 1) Enable FIDO2 method in Entra

1. Entra admin center -> Protection -> Authentication methods -> Policies.
2. Open **FIDO2 Security Key**.
3. Set **Enable = Yes**.
4. Target `SG-Admins-FIDO2-Pilot`.
5. Configure key restrictions (AAGUID allow list) for approved key models.
6. Save.

### 2) Create authentication strength

1. Entra admin center -> Protection -> Conditional Access -> Authentication strengths.
2. Create custom strength: `AS-Admins-Cryptnox-Only`.
3. Include only **FIDO2 security key** (or include WHfB if explicitly approved).
4. Save.

### 3) Create Conditional Access policy

1. Entra admin center -> Protection -> Conditional Access -> New policy.
2. Name: `CA-Admins-Require-Cryptnox`.
3. Users:
   - Include `SG-Admins-FIDO2-Pilot`.
   - Exclude break-glass accounts.
4. Target resources:
   - Start with Microsoft 365 + Azure management apps for pilot.
   - Expand to All cloud apps after validation.
5. Grant:
   - Require authentication strength = `AS-Admins-Cryptnox-Only`.
6. Set to **Report-only** first.

### 4) Validate and enforce

1. Review sign-in logs for pilot users.
2. Confirm success in Office, Entra portal, and admin workflows.
3. Flip policy to **On**.
4. Add remaining admins to `SG-Admins-FIDO2-Enforced`.
5. Update policy include group to enforced group.

### 5) Hardening controls

1. Enable/confirm policy to block legacy authentication.
2. Remove weak fallback methods for admin users where possible.
3. Require compliant/managed admin workstation where applicable.

## Optional: On-prem AD admin logon enforcement

For AD interactive logons, enforce smart card/certificate auth:

1. Issue admin smart card certificates.
2. Set user flag: **Smart card is required for interactive logon**.
3. Test workstation and RDP admin flows before broad rollout.

## Rollback plan

1. Move impacted user out of enforced group.
2. Confirm sign-in restored.
3. Investigate failure in logs.
4. Re-enroll key and retest.

## Audit evidence to retain

- Policy screenshots/exports
- Group membership changes
- Pilot test results
- Sign-in log excerpts showing auth strength enforcement
