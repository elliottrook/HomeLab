# D3 credential custody and finite Mac worker — 2026-10-06

**LOCAL CANDIDATES. No credentials issued, Keychain accessed or deployment made.**
This extends the [gateway assembly](D3-gateway-assembly-2026-10-06.md), not a new
platform or another local-model evaluation.

## Implemented and tested

`credentials.py` supplies two explicit, disabled-by-default adapters:

1. Gateway: read one supplied protected AppRole file, authenticate to the fixed
   OpenBao TLS endpoint using its CA, read only the proposed introspection secret,
   and revoke the short-lived vault token before releasing the value to the
   verifier. Refuse unexpected token policies/lifetimes; attempt revocation even
   if the read or authority check fails. Failed revocation denies credential
   delivery; a five-minute maximum TTL bounds a stranded session. No secret cache.
2. Mac: read only the distinct Keychain service
   `com.elliottrook.aster-codex-worker`, account `authentik-app-password`, through
   `/usr/bin/security`; exchange it at the fixed Authentik token endpoint for
   `aster-codex-worker-mac`, client `aster-codex-worker`, scope `aster.worker`.
   Require a Bearer token of at most five minutes, no refresh token, no fallback.
   The password never enters command arguments or environment. Stderr and
   exceptions are sanitized. The callback runs outside the worker event loop.

The Mac adapter is a same-user custody design, **not isolation from arbitrary
code running as Jason**. Keychain ACL/signing behavior is not yet validated for
this item, and no claim that only the Python worker can obtain it is made. Do not
authorize a broad “allow all applications” ACL. Model tool restrictions remain
necessary. A stronger signed helper may be needed if the approved ACL cannot
support this fixed reader safely; do not silently loosen it.

`connected_worker.py` is a manually started, one-assignment candidate using the
actual HTTPS worker client and credential adapter. Default invocation only emits
disabled metadata. `--prepare` explicitly inspects installed Codex metadata;
`--run` requires the prepared fingerprint and a fresh private evidence directory.
The fingerprint covers every Python module, binary/config/model preflight,
assignment ID, payload and scope. It retains ChatGPT-authentication checks and
the fixed fictional Orion payload, not personal or HomeLab data. No launchd
agent, boot/login trigger, queue discovery, automatic resend or paid API fallback.
The durable gateway ledger must remain intact; a new local run directory is not
permission to recreate or replay an uncertain gateway job.

Validation: **163 delegation tests pass**. Eight custody tests cover fixed paths,
policy/lifetime expectations, cleanup after read failure, failed revocation,
unsafe files, fixed Keychain arguments, malformed tokens, redirects and response
limits. Three connected-worker tests cover inert default, assignment/source
binding and private evidence without answer duplication. All credentials are
synthetic fixtures. Default CLI invocation reported disabled/manual/no inference.
No new live authentication, model run or credential access occurred.

## Exact candidate vault objects

| Object | Proposed scope and limit |
|---|---|
| KV v2 `secret/ai-pam/aster-worker-introspection` | Only `client_secret` for the separate worker OAuth provider; gateway consumer only |
| KV v2 `secret/ai-pam/aster-codex-worker` | Authoritative custody of worker app password; no gateway read grant |
| Policy `aster-worker-introspection-read` | Exact one secret read and token self-revocation; no list, write, admin or default policy |
| AppRole `aster-worker-introspection` | Source and token bound to `192.168.70.10/32`; five-minute token; two token uses (read/revoke); 24-hour SecretID pilot expiry |

Candidate policy/role inputs are
`services/aster-agent/delegation/deploy/introspection-read.hcl` and
`introspection-role.json`. These must create new objects, never overwrite a
pre-existing object discovered at execution. A SecretID supports multiple logins
during its bounded 24-hour pilot; it is not a one-use credential. No automatic
renewal or indefinite unattended service is proposed in this first deployment.

The runtime AppRole material needs a separately reviewed systemd credential
delivery path, with only the Aster service able to read its transient plaintext.
Do not commit it, pass it in argv/env, reuse Forgejo material, or create a static
plaintext bootstrap-file exception. Source-local encrypted provisioning and
recovery must be settled before installing the role. The adapter accepts a path;
that alone does not establish secure delivery of the file.

## Provisioning, validation and recovery sequence

1. Reconcile non-secret existing object metadata and service versions. Abort on
   collisions or configuration drift. Verify recent vault backup/recovery status.
2. Human establishes the documented vault administration ceremony outside chat.
   No recovery shares, decrypted ceremony credentials or root tokens enter AI
   context. Prepare the source-local bounded provisioning helper and credential
   transport before asking the human to unlock anything. No supported alternate
   current admin identity has been established by the repository evidence.
3. After explicit approval, create only the named OAuth provider/application,
   exact worker service account, fixed scope and application binding. Restrict
   application access to that service identity; no human or other worker access.
   Keep cross-provider introspection disabled. App password expiry: 24-hour
   initial pilot. Provider verification secret stays gateway-side only.
4. Transfer generated values directly into their separate approved custody
   destinations, never chat/output/Git. Verify round-trip equality source-locally,
   emitting booleans only. Preserve object IDs and versions, not values.
5. Prove wrong user/client/scope, unrelated vault path, policy administration,
   expired/revoked token and vault outage denials before enabling transport.
   Specifically test whether the app password can authenticate to another client;
   if it can, tighten issuer policy before proceeding, not merely rely on Aster.
6. Confirm vault-token cleanup and human administrative-session closure. Record
   expiry and revocation identifiers. Mount gateway only after the credential
   consumers and existing Aster lifecycle are reviewed together.
7. One separately approved fixed-payload job verifies the actual Mac → Aster →
   Codex → Aster path and native owner display. This is integration acceptance,
   not another model-quality or authentication-only experiment.

Rollback: disable delegation first; remove the worker app password and revoke
issued access tokens, disable the new application/account, destroy the dedicated
SecretID and revoke outstanding role tokens, then remove the new runtime delivery
and Keychain item. Retain non-secret audit/object versions and job ledger; never
reset uncertain jobs into the queue. Do not erase existing vault paths, human
login items, other AppRoles or restore an old revoked credential. On uncertainty
keep delegation disabled and reconcile metadata before cleanup/retry.

## Remaining approval blockers and resume

The adapters and manual worker are ready for integration review; **provisioning
is not yet execution-ready**. Remaining work is the source-local provisioning
helper, encrypted runtime credential delivery, Keychain ACL validation, provider
access-binding configuration, gateway mount and a bounded assignment operator.
Human recovery availability has been requested, without asking for secrets.
No production change approval is requested merely to investigate these facts.

## Sources and evidence categories

- VERIFIED REPOSITORY EVIDENCE: prior successful temporary identity tests used
  username/app-password exchange. Existing operational reference records a
  human-only root ceremony and revoked temporary admin tokens; this does not
  establish a currently usable administrative session.
- PRIMARY DOCUMENTATION: [Authentik M2M](https://docs.goauthentik.io/add-secure-apps/providers/oauth2/machine_to_machine)
  describes the username/app-password grant and confidential-provider
  introspection. Its alternative provider-secret grant can create a service
  identity: the introspection credential is sensitive authority, not a harmless
  read-only password.
- PRIMARY DOCUMENTATION: [OpenBao AppRole](https://openbao.org/docs/auth/approle/)
  and [API](https://openbao.org/api-docs/auth/approle/) describe policy and login
  constraints. The repository's existing gateway demonstrates the API shape.
- PROPOSAL: all permanent object names, TTLs, custody locations and runtime
  integration above. They are not claims of existing live state.
