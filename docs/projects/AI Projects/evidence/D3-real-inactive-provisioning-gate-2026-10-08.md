# D3 — real inactive worker provisioning package

Status: PREPARED, NOT EXECUTED. Jason's latest approval followed an offer to
prepare real setup. This document now makes the production mutations concrete;
obtain explicit confirmation of this scope before making them.

## Outcome and limits

Create the credentials and inactive identity needed for Aster's future
subscription-backed Codex connection. Success is protected credential custody,
revoked temporary administrative authority and a worker that is still inactive.
It is not an activated assistant, a model call, or sysadmin authorization.

Earlier evidence covers local contracts (226 tests), actual engine provisioning,
actual two-share ceremony, lost-response recovery, cross-host pipe success and
failure, fictional Keychain custody and encrypted gateway custody. Do not repeat
these passed primitives. Actual production integration is not yet verified.

Read-only preflight on 2026-10-08 found all three source staging paths absent,
117's temporary handoff absent, 104's destination credential absent and its
credential directory mode 0700. Authentik preflight passed: new names absent,
21 existing applications with reviewed access bindings, signing key present.
No credentials or private recovery files were read. Final preflight must repeat
immediately before execution because these facts can change.

## Exact grouped approval requested

Authorize ONE attempt, with pause for Jason's private inputs, of the following:

1. Recheck AI-PAM readiness, OpenBao 2.6.4/unsealed, all proposed names/paths
   absent, source fingerprints, installed tools and private directory ownership.
   Check only the fixed Mac Keychain item for absence, suppressing all command
   output and inspecting its status code; do not retrieve an existing password.
   Existing or uncertain items stop the operation before any replacement.
2. Create one fresh Proxmox recovery snapshot on each LXC 104, 106 and 117 named
   `aster-worker-preprovision-20261008`, with a description of this inactive-worker
   setup. Verify snapshot presence; do not overwrite or delete backups. No service
   stop/restart is authorized. Snapshot failure stops setup. These checkpoints
   are not permission for whole-system rollback or evidence of a new restore test.
3. Stage the 14 source files below, root-owned directory mode 0700/files 0600,
   under `/var/tmp/aster-worker-provision-20261006` inside 104, 117 and the existing
   `authentik-server-1` container on 106. Verify archive and every source hash;
   do not overwrite. No packages, permanent units or scheduled jobs are installed.
4. Prepare local private `.aster-local-state/` mode 0700 in this worktree, compile
   the existing Swift installer in advance to verify tool availability, and keep
   it private. The controller will compile its own copy in the fresh run directory.
   This ignored local directory must not be committed or uploaded.
5. Stop for Jason's private terminal. Verify the public helper fingerprint before
   he supplies human AppRole RoleID/SecretID and two distinct decrypted shares.
   Helper uses authenticated loopback TLS only, creates exact new policies/role,
   issues a 600-second scoped setup token, revokes the generated root, then writes
   only the scoped token to `/run/aster-worker-provision/admin.token` (root 0600
   in a fresh root 0700 directory). No root or share enters this chat or controller.
6. On Jason's non-secret completion confirmation, promptly run the exact controller
   once with the fingerprint below. Its private child-process pipes may carry the
   newly generated application credentials, never recovery shares/root tokens.
   Do not print child frames, command output containing secrets, or response bodies.
7. Verify complete journal, source-local admin removal/revocation receipt, exact
   inactive identity/binding metadata, encrypted destination ownership and fixed
   Keychain round-trip receipt. Recheck AI-PAM health and disabled delegation.
   No authentication/model pilot or identity activation follows automatically.
8. Preserve sanitized object IDs/stages/results as evidence. Remove exactly the
   14 staged source files and their directories after matching inventory/hashes.
   Preserve the human stage journal and snapshots for recovery; do not silently
   delete an unexpected handoff file or partially provisioned object.

## Objects that will be created

| Location | Exact objects / lifetime |
|---|---|
| Authentik 106 | Inactive service account `aster-codex-worker-mac`; application slug/client ID `aster-codex-worker`; provider `Aster Codex Worker`; scope mapping `Aster Codex Worker Scope` for `aster.worker`; one positive user binding; app-password token `aster-codex-worker-pilot`, 24 hours |
| OpenBao 117 | Read policy `aster-worker-introspection-read`; AppRole `aster-worker-introspection`; temporary policy `aster-worker-provision-once`; two new KV v2 records `secret/data/ai-pam/aster-worker-introspection` and `secret/data/ai-pam/aster-codex-worker`, version 1 with CAS zero |
| OpenBao authority | Scoped setup token at most 600 seconds, explicitly revoked after provisioning; AppRole SecretID 24 hours, bound to broker `192.168.70.10/32`; issued read tokens at most five minutes, two uses |
| Gateway 104 | New host-encrypted `/etc/credstore.encrypted/aster-worker-approle`, containing only runtime RoleID/SecretID; no service enabled to consume it |
| Mac Keychain | New non-synchronizing service `com.elliottrook.aster-codex-worker`, account `authentik-app-password`; explicit `/usr/bin/security` reader; the existing same-user security boundary still applies |
| Local journal | `.aster-local-state/worker-provision-20261008/stages.sqlite`, mode 0600; stage names and object IDs only, no credential values |

The temporary setup policy remains inert after token revocation; deleting it
would require additional administrative authority and is not silently performed.
Other new fixed policies, KV records and encrypted/Keychain items persist. The
pilot password and SecretID expire after 24 hours; expiry does not delete stored
copies. Do not create them until Jason is present and the next integration window
is practical. If expiry occurs first, design one targeted renewal operation;
never replay this create-only controller.

## Frozen package and execution references

Archive `/private/tmp/aster-worker-real-provision-20261008.tar`, SHA-256:
`8a13a9c0ef517a2d7744d23b0f218fa47b498c31705b66046fca7e839830df79`.

Members are `provision_controller.SOURCES` (11 files) plus `admin_bootstrap.py`,
`human_ceremony.py`, `human_root_recovery.py`. The recovery helper is staged for
availability, but running it or revoking any additional token requires an
incident-specific human decision; this setup does not authorize general cleanup.

Controller fingerprint:
`e3f26576f2f58fb2c579ee46ea6bf6380089518e39bcf97c910930ddfae1f6b2`

Human helper fingerprint:
`52de5e20803eceeabb53244b5918442bb789b646ae1f2e538405f87a7a6da482`

Human command, ONLY after approval, staging and an explicit ready notice:

```sh
ssh -t proxmox
pct enter 117
python3 -B /var/tmp/aster-worker-provision-20261006/human_ceremony.py --run --approved-sha256 52de5e20803eceeabb53244b5918442bb789b646ae1f2e538405f87a7a6da482
```

Enter private values only into the hidden prompts, not as shell commands. Use
`human-root-ceremony-approle.pgp` and two distinct `recovery-share-*.pgp` files.
Do not decrypt private-key `.asc` exports or reuse historical root tokens.
Say only “setup ready” after the helper reports ready/root revoked. Otherwise
say “setup stopped”; do not send terminal contents. Retain encrypted originals;
remove temporary decrypted copies and clear clipboard after private use.

## Failure, recovery and acceptance

- Any failed precondition stops before the dependent mutation. No guessed fix,
  policy widening, second attempt or overwrite is covered by this approval.
- During the human ceremony, keep other root-generation ceremonies paused.
  Its successful root revocation precedes handoff. If completion is uncertain,
  stop; the tested human-only recovery helper supports explicit target revocation,
  but metadata alone cannot establish token ownership. Prepare a concrete private
  review of incident timing/audit evidence/known administrator tokens. Jason is
  not expected to guess which identifier to revoke. Additional token revocation
  requires specific authorization after that review.
- If the 600-second token expires before controller start, do not create another
  root or run the controller. Existing bootstrap objects require reconciliation.
- A disconnected controller can leave inactive identity objects or encrypted
  credential copies. Preserve journal/object IDs, keep worker inactive and
  delegation disabled, inspect exact metadata, then propose targeted cleanup.
  Do not restore a vault snapshot as an automatic rollback: this can resurrect
  revoked credentials and discard unrelated changes.
- No authority expands on failure. The inactive worker is the containment state.
  After success, require `complete=true`, `worker_active=false`,
  `delegation_enabled=false`, `model_calls=0`, and healthy existing services.
- Local journals live in a managed worktree. Before any worktree archival, retain
  required sanitized provenance durably; ignored local state is not in Git.

Production policy/role absence is checked by the privately authenticated bootstrap;
it cannot be established now without administrative credentials. Actual Keychain
absence and snapshot success remain final preconditions, not current claims.

## Next boundary

After this succeeds, prepare the disabled gateway/worker deployment and a narrowly
approved authenticated pilot. Enabling the identity, enabling delegation, granting
tools, service changes, model calls and Git pushes are outside this scope.
