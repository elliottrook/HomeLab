# D3 — one completed-answer recovery trial gate

**Status: PREPARED LOCALLY; NOT APPROVED OR DEPLOYED.** Owner: Jason. This is a
one-time recovery of the already completed fictional Orion answer, not permission
to infer, submit a new request, open sysadmin tools or run a standing worker.

## Why this is a separate gate

The gateway deliberately keeps answer text in memory for only 15 minutes.
Restart removed the visible answer while retaining completion metadata and its
SHA-256. The old Mac dispatch record still identifies the original completed
thread/turn, and a metadata-only preflight confirms ChatGPT subscription mode.
The previous approval covered the original turn and cleanup, not renewed worker
access or a new production route. Recovery reads the **original stored turn**;
it makes no model call. A read can still fail if that history disappears or
access changes. One successful read would prove this path once, not appliance
reliability or lasting answer storage.

## Current baseline to recheck immediately before change

- Gateway LXC 104 is active; 44 scoped routes; new request intake is closed;
  recovery route is absent. Existing completed records remain. The corrected
  delegation pilot drop-in stays in place; request-enabling drop-in stays absent.
- Worker identity on Authentik 106 was last checked inactive with zero grants.
  Recheck before any activation. The existing worker application password
  expires **2026-10-09 19:02 Vancouver**; do not renew it under this gate.
- Only `orion-connected-20261008`, completed, is in scope. The last read-only
  gateway digest check returned
  `c455990de30fcc3d023ce20da2aff98c901fd7d285185335553f2252e7976abe`.
  The Mac dispatch database is private mode 0600 and has that completed job.
  No prompt, answer, thread content, token or secret is placed in this document.
- Live gateway source pre-change SHA-256 (2026-10-08 read-only):

| File under `/opt/aster-agent/delegation/` | SHA-256 |
|---|---|
| `deployment.py` | `920396077681fde497d6ff8f3284ee3c133fe150eda5f685f39e75c499bc704c` |
| `gateway_assembly.py` | `380e746a6128090ef772286c4ed8d73a4600c9af8cdf80b24548e7d4ad0290a1` |
| `request_intake.py` | `5d0678494faeb621bf932aa9b7ae01fcbf9907fe5b9860cca899fcc2c43db33b` |
| `handoff.py` | `79a23cf28fad0409e0316e249333ae149d18a2281dfedfb060c4c496529834ba` |

If any baseline hash, job state, identity state, credential validity or backup
condition differs, stop and revise this gate. Do not blindly apply the candidate.

## Exact candidate and impact

1. Create a private recovery checkpoint of the four gateway modules, current
   systemd drop-in state, Gateway SQLite database using SQLite backup, and
   installed Companion app. Refuse an existing checkpoint path. Do not print
   database or credential contents. Record hashes and ownership.
2. Install only the four changed gateway modules plus new `recovery_router.py`
   under `/opt/aster-agent/delegation/`, and only the new
   `aster-answer-recovery.conf` service drop-in. Keep request intake disabled.
   `handoff.py` also adds an unused supervised-session table/methods; no session
   route is mounted. This is a schema side effect to review. Reload systemd and
   restart **only** `aster-agent` once; verify healthy status, prior routes,
   two completed records, owner authentication, worker isolation and no new
   request submission. Anonymous recovery must be denied.
3. Back up the installed Companion bundle and install signed local build 8
   only if its whole-bundle signature/hash matches the pinned candidate. Verify
   normal sign-in and that Ask Codex remains disabled. Recovery button is shown
   only for a completed missing-answer job while the flag is enabled.
4. Prepare and pin the Mac recovery runner against the original private job,
   gateway digest, installed Codex binary/account and exact source hashes.
   Preparation uses no Keychain credential and no inference. Recheck its
   fingerprint immediately before execution; do not approve a changed scope.
5. Activate only the existing bounded worker identity using the prior verified
   procedure. Jason explicitly clicks **Recover original answer** on the
   fictional Orion job in Companion. This creates one four-minute ticket.
   Operator starts the pinned runner once with that ticket, and Jason grants
   only the expected one-time Mac Keychain prompt if shown. No automatic retry,
   model turn or history listing is permitted. The original answer may be
   delivered only after owner/job/thread/turn/digest verification.
6. Jason checks the visible answer and copies it to a private location if he
   wants to keep it. **This trial does not add durable answer storage.** After
   acceptance or failure, deactivate the worker, verify zero grants, remove
   only the exact recovery drop-in, reload/restart Aster once, verify status and
   closed intake. The gateway restart erases the recovered volatile answer;
   that limitation must be understood before cleanup.

Candidate source SHA-256 (recompute after any edit):

| File | SHA-256 |
|---|---|
| `deployment.py` | `1601a4ca4e06db910f8bff2b4a188c2a3113816529aa94c1009850ba4574e047` |
| `gateway_assembly.py` | `56f45e931ff8c844e1f4230eade1e60828c4f92d8366614bfb2845df7840fd93` |
| `request_intake.py` | `6ddfe7ce45256dc66edc2703bb87e379fc9759f81fd9b56f31f7fb5cd27f5528` |
| `handoff.py` | `3941c451d0ea1978462bc87b4769dfa622dd983b6a4a78eee275cc562482fbfd` |
| `recovery_router.py` | `031eec7c8938d5aaf671107da060578cb30bef9847d0358e084a28d599647346` |
| `deploy/aster-answer-recovery.conf` | `961ae1416bd070896f4050d82fc108b5a132ffe4245a8ee38480bc56d0dd62a3` |
| Local signed build 8 executable | `343830529ba2836a741268bb8a1566a8ad093f1a2fb0fc460324eaaa2e07705b` |

Local candidate app: `/private/tmp/aster-native-recovery-candidate-20261008/AsterCompanion.app`.
The worker source is pinned separately by the preparation manifest. Preparation
passed with ChatGPT account, native OpenAI provider, zero enabled MCP servers,
read-only sandbox and zero model turns. No ticket, Keychain read or recovery
occurred. Final metadata-only preparation SHA-256:
`ebe896e52addbeb25f4e0c42aaf2e8ccc945e620265ab03ff445715058727d47`.
Recompute/review it immediately before running; it is not authority by itself.
282 backend tests and 35 native tests pass.

## Acceptance, stop and recovery

Accept only if the original answer digest matches and Jason sees the answer,
with one ticket, no new Codex turn, no request submission, no permissions/tools,
and worker grants revoked after the trial. Record timing, exact source/manifest
hashes and sanitized status only. Do not record answer text or hidden reasoning.

On mismatch, timeout, uncertain claim, auth failure, unexpected new route,
identity residue, service failure or UI failure: **stop**. Do not reissue a
ticket or run the worker again. Reconcile status and access read-only, revoke
the worker, remove the exact recovery drop-in, reload/restart the gateway once
and restore only changed gateway source and Companion bundle from checkpoints
if needed. Extra SQLite tables may remain; restoring the entire database could
discard newer receipts and requires a distinct data-recovery decision. Preserve
all checkpoints and the uncertain ticket for analysis.

No Git push, secret renewal, general sysadmin capability, permanent recovery
service or expanded agent permissions are included. Human approval must be
explicit for this one bounded live change. A later durable-answer design needs
its own privacy/retention decision and evidence.
