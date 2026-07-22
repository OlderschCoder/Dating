# User Step-by-Step: Configure Cryptnox/FIDO2 for Admin Sign-In

This guide is for admin users who must sign in with a security key (instead of password-based MFA).

## What you need before starting

1. Your company admin account (for example `name@company.com`).
2. Your Cryptnox FIDO2 security key (and backup key if issued).
3. A supported browser (Edge, Chrome, or Firefox current version).
4. USB port or NFC-capable device (depending on key type).

## Part 1: Register your primary key

1. Open:
   - `https://mysignins.microsoft.com/security-info`
2. Sign in with your work account.
3. Select **Add sign-in method**.
4. Choose **Security key**.
5. Choose key type:
   - **USB device** if you plug in key, or
   - **NFC device** if using tap on supported device.
6. When prompted, insert/tap your Cryptnox key.
7. Create or enter the key PIN.
8. Touch or confirm on the key when prompted.
9. Name the key (example: `Cryptnox-Primary`).
10. Confirm registration completed successfully.

## Part 2: Register your backup key (strongly recommended)

Repeat Part 1 with your second key and name it:

- `Cryptnox-Backup`

## Part 3: Verify sign-in works

1. Sign out of Microsoft 365.
2. Go to `https://office.com`.
3. Select sign-in and choose **Security key** method.
4. Insert/tap key, enter PIN, complete key prompt.
5. Confirm you can open Outlook/SharePoint/Teams.
6. If you are an Azure admin, also test:
   - `https://entra.microsoft.com`
   - `https://portal.azure.com`

## Part 4: Optional laptop biometric flow

If your policy allows Windows Hello/passkey as approved method:

1. At sign-in prompt choose passkey/biometric option.
2. Use fingerprint/face/Windows Hello PIN.
3. Confirm successful sign-in.

If policy requires hardware key only, biometric-only options may be blocked.

## Daily sign-in instructions

1. Start sign-in with your work account email.
2. Choose **Security key** when prompted.
3. Insert/tap key.
4. Enter key PIN.
5. Touch/confirm key.
6. Continue to application.

## If your key is lost, stolen, or not working

1. Report immediately to helpdesk/SOC.
2. Use backup key if available.
3. Do not keep retrying unknown prompts.
4. Helpdesk will remove old key, issue replacement, and re-register.

## Security rules

1. Never share your key or PIN.
2. Do not approve unexpected prompts.
3. Keep backup key in a separate secure location.
4. Report suspicious sign-in attempts immediately.
