# D3 — private human ceremony preparation and isolated test gate

Status: APPROVED ISOLATED TEST PASSED; approval consumed. No production ceremony,
credential provisioning, delegation activation or Git push performed.

## Executed result — 2026-10-08

Jason approved the exact isolated scope in this chat. The archive hash and all
nine member hashes were checked before staging, then checked on the destination.
The reviewed runtime unit started once and exited successfully (status 0).

```json
{"passed":true,"version":"2.6.4","threshold":2,"shares":3,"initial_root_revoked":true,"generated_root_revoked":true,"human_session_revoked":true,"scoped_admin_revoked":true,"production_contacted":false,"real_credentials_used":false}
```

The test verified revocation through subsequent denied API requests, not merely
successful revoke responses. Production configuration, data, keys and recovery
files were not accessed. Startup sampling observed about 55 MiB memory and
0.65 CPU seconds; final resource counters were unavailable after unit exit, so
these samples are not final peak/total claims.

Cleanup checked exact inventory and hashes before removing the nine files,
their two directories and the runtime unit. Independent verification returned
`LoadState=not-found`, `ActiveState=inactive`, `MainPID=0`; staging was absent.
AI-PAM passed before and after: vault unsealed, Authentik reachable, exact policy
catalogue, zero active requests and 37 recorded outcomes. Nothing was pushed.

This closes compatibility of the normal authenticated two-share path with
OpenBao 2.6.4. It does not close the interruption recovery limitation below or
verify the live human AppRole's exact policy/expiry.

## Purpose and evidence

The remaining setup needs temporary administrative authority without exposing a
root token to Codex. `human_ceremony.py` prompts only in Jason's private terminal,
authenticates with the existing human ceremony AppRole, accepts two distinct
shares, decodes the resulting root token in memory and passes it directly to the
bounded bootstrap. Bootstrap revokes root before delivering its 600-second scoped
provisioning token to a root-only source-local file. No recovery values are printed.

219 local delegation tests passed on 2026-10-08. Eight new fictional tests cover
successful decoding, wrong scope, an existing ceremony, duplicate shares, lost
start/final responses, interruption and root-lookup failure. Review fixed a real
cleanup gap: bootstrap now attempts fresh-token revocation even if its first
lookup fails. The human helper checks policies in the login receipt rather than
requiring lookup-self permission from the deliberately narrow human identity.

Production controller transport now explicitly selects container root and disables
bytecode writes, matching root-only source custody. This remains a LOCAL change;
it neither grants an AI root authority nor changes deployed Authentik permissions.

Read-only preflight confirmed installed OpenBao 2.6.4 and absent proposed staging.
The prior successful isolated dev-server test did not exercise two-share root
generation. The new test targets that missing integration only.

## Exact approval requested

One isolated rehearsal on existing LXC 117, with the existing `/usr/bin/bao`:

1. Check staging and unit absent and production health unchanged.
2. Stage the nine files named by `isolated_ceremony_rehearsal.SOURCES` under
   `/opt/aster-ceremony-isolated-20261008`; root-owned directories 0755 and
   non-secret source files 0644, readable by the dynamic fixture user. No overwrite.
3. Verify archive and individual source hashes. Copy the reviewed unit to
   `/run/systemd/system/aster-ceremony-isolated.service`, reload unit metadata,
   and start it ONCE. Do not enable it.
4. Unit creates an entirely separate in-memory vault in a private network and
   temporary-files namespace. Initialize disposable 2-of-3 shares, unseal only
   that fixture, create its fictional human identity, revoke its initial root,
   and exercise the actual helper through generated-root/scoped-token revocation.
   All fixture credentials stay in process memory. Output is allowlisted results.
5. Capture outcome, stop only this unit if needed, remove its runtime unit and
   enumerated source files, reload unit metadata and verify unit/process/staging
   absence. Stop on unknown files. Recheck production readiness.

Limits: 120 seconds runtime, 512 MiB memory, no swap, 50% CPU, 128 tasks,
unprivileged dynamic user, no capabilities, no core dumps, read-only system,
production vault paths explicitly inaccessible. Private loopback port 38200;
no access to production port 8200 or LAN. No production restart, real secrets,
real identity changes, model calls, Keychain access, activation or push.

Archive: `/private/tmp/aster-ceremony-isolated-20261008.tar`

SHA-256: `85de84748fbc20e2055353b38ad1b2cc6811051d9e91e1d214218f8cd1825a4f`

Approval is required by AGENTS.md for remote writes. Rollback is bounded fixture
termination and enumerated cleanup; the fixture database disappears on exit.
Success requires two-share completion plus independently checked rejection of
the initial root, generated root, human session and scoped administrator token.
Failure is retained as failure, without retry or production changes.

## Real setup and interruption rules — candidate, not execution instructions

Do not open a real ceremony yet. First pass this isolated test and assemble the
complete real provisioning gate with hashes, custody destinations and recovery
checkpoints. Verify the actual human login policy/expiry privately; current
repository evidence establishes the AppRole's purpose, not every live field.
The fixture deliberately grants only ceremony and self-revoke operations.

When separately authorized, Jason uses a private terminal outside agent capture.
He decrypts `human-root-ceremony-approle.pgp` and two distinct
`recovery-share-*.pgp` files privately. The `.asc` private-key exports are not
shares, and historical encrypted root-token files contain revoked tokens.
Prompts accept role ID, SecretID, share one and share two without echo. Do not
paste values into chat, shell arguments, environment variables or screenshots.
Keep encrypted originals; remove temporary plaintext and clear clipboard after
use. A currently unsealed production vault does not need unsealing again.

The helper writes only stage names into root-only
`/run/aster-worker-provision/ceremony-stages.jsonl`. This is interruption evidence,
not durable audit storage: preserve sanitized stages before reboot/cleanup.
Never blindly rerun an existing setup directory or overwrite existing objects.

| Last confirmed boundary | Required handling |
|---|---|
| Before ceremony start | Confirm no new attempt exists; no claim that a timed-out login created no session. Session expiry must be verified privately. |
| Start attempted, no receipt | State unknown. Do not cancel another person's attempt. Human reconciliation must establish ownership. |
| One share accepted | Handled interruption checks matching nonce before cancellation and revokes the human session. Abrupt death still requires private verification. |
| Final share attempted, no receipt | A root token may exist despite no response. Cancelling an attempt does not revoke an already issued token. Stop; private administrator reconciliation is required. |
| Root delivered to bootstrap | Bootstrap owns handled cleanup, including lookup failure. Process kill/power loss cannot guarantee revocation. |
| Scoped token delivered | Root revocation was confirmed first. Scoped token expires within 600 seconds; incomplete objects remain for explicit reconciliation, not automatic deletion. |
| Controller incomplete | Use its recorded identity IDs and attempted/confirmed stages to inspect exact objects privately. Keep the user inactive and delegation disabled; never infer rollback from disconnect. |

**Open recovery limitation:** safe identification/revocation of an issued root
after a lost final response or abrupt process death is not yet a tested operator
procedure. Production provisioning remains blocked until that procedure is
concrete; this isolated happy-path test alone cannot close it. No general token
listing, broad revocation or restoration of old vault state is authorized.

## Primary sources and uncertainty

- [OpenBao 2.6.4 API implementation](https://github.com/openbao/openbao/blob/v2.6.4/api/sys_generate_root.go): authenticated endpoints, nested response data and PUT requests. Version-specific source governs over current documentation examples.
- [Root generation API](https://openbao.org/docs/api/system/generate-root-token/): OTP encoding and threshold ceremony. Current documentation identifies itself as 2.7.x; compatibility is a test hypothesis.
- [In-memory storage](https://openbao.org/docs/configuration/storage/in-memory/): disposable fixture storage, never proposed for production.
- [Initialization API](https://openbao.org/docs/api/system/init/): fixture share count and threshold.

External sources checked 2026-10-08. Normal 2.6.4 ceremony compatibility is now
verified by the isolated result above; local unit tests alone did not establish it.

## Follow-up source inspection: lost final response

Version-pinned [root generation source](https://github.com/openbao/openbao/blob/v2.6.4/vault/generate_root.go)
creates the root, encodes it and deletes the active generation record upon
completion. Cancellation cannot be treated as revoking the resulting token.
The [token store](https://github.com/openbao/openbao/blob/v2.6.4/vault/token_store.go)
creates that root with display name `root`, path `auth/token/root` and a creation
timestamp. Those fields identify a class of token, not uniquely this ceremony.

ARCHITECTURAL INFERENCE: a separately authorized private recovery operation could
use token accessors and metadata to locate and revoke an orphan, but automatic
selection by time/name alone would be unsafe. Do not introduce broad token
enumeration into normal Aster provisioning. Develop and test a human-only,
explicitly targeted recovery procedure before production setup; no permission
for production enumeration or revocation follows from this successful fixture.
