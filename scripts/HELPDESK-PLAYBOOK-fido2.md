# Helpdesk Playbook: Admin FIDO2 Enrollment and Support

Use this playbook to onboard and support privileged users required to use FIDO2 security keys.

## 1) New admin onboarding checklist

1. Verify identity using approved internal process.
2. Confirm user is in the correct pilot/enforced admin group.
3. Assign two keys:
   - Primary key
   - Backup key
4. Record key serials/asset IDs in asset tracker.
5. Send user the configuration guide:
   - `scripts/USER-STEP-BY-STEP-CONFIGURATION.md`

## 2) Assisted registration workflow

1. User signs in at `https://mysignins.microsoft.com/security-info`.
2. User adds **Security key** method.
3. User chooses USB or NFC flow.
4. User sets key PIN and touches key when prompted.
5. User names key (`Cryptnox-Primary`).
6. Repeat for backup key (`Cryptnox-Backup`).
7. Verify both keys appear in Security Info.

## 3) Validation checklist

1. Test Office sign-in (`https://office.com`) with key.
2. Test Entra portal sign-in for admins (`https://entra.microsoft.com`).
3. Confirm user can complete required admin tasks.
4. Confirm password fallback is blocked by policy.

## 4) Common issues and fixes

### Issue: User cannot register key

- Check user is targeted by FIDO2 authentication method policy.
- Check key model/AAGUID allowed in restriction policy.
- Confirm browser supports WebAuthn/FIDO2.

### Issue: User prompted for password instead of key

- Verify user is in enforcement group.
- Verify CA policy is On and includes target app.
- Verify policy exclusion does not unintentionally include the user.

### Issue: Key works on one device but not another

- Confirm browser/device has FIDO2 support enabled.
- Update OS/browser.
- Try alternate USB port/NFC reader.

### Issue: Token claim method mismatch

- Review Entra sign-in logs and authentication details.
- Confirm authentication strength configuration.

## 5) Lost or stolen key procedure

1. Suspend access risk: user reports immediately to SOC/helpdesk.
2. Remove lost key from Security Info.
3. Revoke smart card cert (if used for AD login).
4. Issue replacement key and register it.
5. Validate sign-in success.
6. Document incident ticket and closure evidence.

## 6) Break-glass escalation

1. Only security leadership can authorize break-glass use.
2. Record reason, approver, start/end time.
3. Monitor and alert on break-glass account sign-ins.
4. Rotate break-glass credentials after use.

## 7) Deprovisioning

1. Remove user from privileged admin groups.
2. Remove registered security keys from account.
3. Reclaim physical keys and update asset records.
4. Disable or archive account per offboarding policy.
