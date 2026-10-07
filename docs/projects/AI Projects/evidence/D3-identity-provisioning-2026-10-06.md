# D3 inactive identity and Mac installer checkpoint

**LOCAL CANDIDATES. No identity or credential created.**

## Verified observations

Read installed Authentik 2026.8.0 source on LXC 106:
`providers/oauth2/token/client_credentials.py`, `token/base.py`, `views/token.py`.
The username/app-password path requires an active user and application policy
approval; it checks configured grants and intersects requested scopes with the
provider's mappings. A provider without an application is denied by this path.
This is source evidence, not a new authentication experiment.

Live non-secret metadata showed 20 applications supporting client-credentials or
password grants. All had exactly one enabled positive user-only binding. A new
distinct user cannot match those existing user bindings; this inference does not
cover other protocols, future apps or arbitrary policy changes. The unbound-app
default permits access, so the provisioning guard rejects any unbound eligible
application. No existing application or global setting was changed.

The actual `identity_provision.preflight()` ran read-only in the installed
`ak shell`: proposed names available, signing key available, all 20 applications
passed. No credentials returned. A first direct Python model import failed because
Django was not initialized; subsequent inspection used source files and `ak shell`.

## Implemented locally

`identity_provision.py` creates only the new worker, provider, scope, application,
user binding and 24-hour app password. The worker is **inactive**. Its database
transaction completes before protected delivery, so external failures retain an
inactive identity and object IDs for reconciliation. Successful delivery does
not activate the identity. No existing human/provider settings change.

`deploy/InstallWorkerCredential.swift` accepts the password only through a private
stdin pipe. Default invocation does not access Keychain. Install mode creates only
the distinct worker item, refuses overwrite, disables synchronization and uses an
explicit `/usr/bin/security` trusted-reader ACL. It emits no secret and does not
claim an unperformed round-trip verification.

This is a **same-user custody design**, not protection against arbitrary code run
as Jason. Before D4 tool-enabled Codex operation, prove isolation from this reader
or replace it with a narrower credential service. Passing a no-tools pilot does
not authorize that expansion.

## Validation and limitations

- 174 local delegation tests pass. New tests cover conservative access guard
  shapes and refusal without an exact approved fingerprint.
- Real installed-ORM preflight passed. The new provisioning mutation has not been
  exercised against Django; local guard tests do not validate real creation.
- Swift helper compiled and default invocation returned
  `enabled:false,keychain_accessed:false`. No Keychain query/write occurred.
- Compiler warns about deprecated legacy Keychain ACL APIs/noninteractive query
  constant. This candidate needs actual ACL/prompt validation before activation;
  never work around failure with an allow-all-applications ACL.

## Remaining critical path

1. Protected controller joining inactive identity creation, source-local vault
   administration, encrypted gateway delivery and Mac receipt. Its stage journal
   must survive interruption; no automatic issuance retry after lost acknowledgement.
2. Complete runnable human recovery instructions. The repository records the
   ceremony requirement but not the full procedure. Sibling reference/wiki
   Markdown searches found no matching guide. This is a documentation gap,
   not permission to reuse revoked credentials or request secrets in chat.
3. Gateway mount, bounded assignment, identity activation and independent denial
   checks in one reviewed deployment. No new approval is requested yet.

Jason confirmed recovery keys are available. Keep the ceremony closed until the
controller is ready. No production write, real credential access, model call,
dependency installation or push occurred in this checkpoint.
