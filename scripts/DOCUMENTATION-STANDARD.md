# Documentation Standard (Feature Delivery Requirement)

## Policy

Every new feature or behavior change must include documentation updates in the same change set.

## Required documentation actions per feature

1. **User-facing usage updates**
   - Update command examples and options in `README-aruba-account-maintenance.md`.
2. **Security/control impact updates**
   - Update `EXECUTIVE-CISO-BRIEF-network-admin-auth-and-rotation.md` when risk/control posture changes.
3. **Operational procedure updates**
   - Update SOP/playbook/user guide documents if workflows change:
     - `ADMIN-SOP-fido2.md`
     - `HELPDESK-PLAYBOOK-fido2.md`
     - `USER-STEP-BY-STEP-CONFIGURATION.md`
4. **Discovery/monitoring output updates**
   - Document any new report outputs, statuses, and fields.

## Pull request checklist (mandatory)

- [ ] Feature behavior documented
- [ ] CLI/options documented (if changed)
- [ ] Security implications documented
- [ ] Operational runbook updated (if process changed)
- [ ] Examples tested and still valid

## Enforcement rule

A feature is not considered complete until documentation updates are committed and pushed with the implementation.
