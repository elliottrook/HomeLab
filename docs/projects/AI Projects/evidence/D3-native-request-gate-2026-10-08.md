# D3 — Native Companion reviewed-request candidate

Status: NATIVE ROUND TRIP ACCEPTED; approved cleanup complete. Owner: Jason. One-turn approval consumed.
This checkpoint supersedes older next-action prose, not historical evidence.

## Outcome and boundary

Jason selected the native Aster Companion app. The accepted Orion round trip
proved connectivity and answer visibility, not general sysadmin competence.
The next experiment is one user-authored, public/synthetic question reviewed and
explicitly submitted through Companion, with its answer returned to Companion.
No tools, chat-history attachment, background worker, paid API fallback or
infrastructure authority is introduced. D3 does not graduate on this experiment.

## Local implementation

Companion 0.3.0 build 5 exposes Ask Codex, immutable text review and explicit cloud
consent. It saves only the pending request ID before submitting, blocks automatic
resubmission, and restores status after reopening. The new intake authenticates
the owner, binds a UUID and exact UTF-8 text digest, disallows caller-selected
models/tools/owners, and limits text to 16,000 UTF-8 bytes. Duplicate requests
cannot create another assignment; different text under an existing ID conflicts.
Worker payload retrieval requires the assigned worker and offered delivery ID.
The launcher verifies text digest, model and scope before constructing the agent.

Gateway request text is memory-only, expires after 240 seconds and is swept every
five seconds. Restart does not restore it. The assignment ledger retains metadata.
Offered/running jobs are not falsely labelled expired by the unclaimed-job sweep.
Answers retain the existing 15-minute in-memory delivery window. Codex itself uses
non-ephemeral threads: questions and answers can remain in Codex/account history.
The native consent copy discloses this; memory-only gateway storage is not a claim
of end-to-end zero retention. Operator evidence must exclude question/answer text.

A failed network submission with no confirmed admission remains pending until an
operator reconciles it; there is no blind retry/reset button. The pending ID is
not multi-user namespaced. This is a single-owner supervised candidate. Existing
ledger capacity and answer recovery limitations preclude general availability.

## Verified baseline

Read-only preflight found installed Companion 0.2.2 build 4, ad-hoc signed; binary
SHA-256 `461cb2c722dee40847d20b4bde27019bab36f1dfcd8f51769c207097d486590d`.
The proposed `AsterCompanion.pre-codex-20261008.app` backup does not yet exist.
The older pre-AI-PAM backup must remain untouched. Primary-checkout build script
has separate signing changes; those are not incorporated or overwritten here.

Gateway 104 was healthy with exactly one completed pilot job. Native intake module
and requests drop-in were absent. Installed module SHA-256 values:

| Module | SHA-256 |
|---|---|
| deployment.py | 221bd433a5ffd531268dd08877ac4393ba531c182dfbae6ae1da11c458b426cc |
| gateway_assembly.py | 83172620a7e0a5cc4e737775271bde56681cd47f961ab80b1e9ea29508966b8c |
| handoff.py | 99a3c43843bc62a72091ce1b742bb9602f63bbf5818135b0afff02b8de393d8d |

Do not overwrite the live main Aster module, credentials.py, or existing pilot
drop-in. Only the above three modules plus new request_intake.py are proposed.

## Approved bounded scope

1. Revalidate hashes, health, installed app, inactive worker and credential expiry.
   Stop on drift or expired credentials; no renewal is included.
2. Preserve and verify the installed whole app at
   `/Applications/AsterCompanion.pre-codex-20261008.app` and the three gateway
   modules/configuration at `/var/lib/aster-delegation-checkpoints/native-requests-20261008`.
   Refuse to overwrite an existing recovery checkpoint.
3. Install only the four frozen gateway modules and
   `/etc/systemd/system/aster-agent.service.d/aster-delegation-requests.conf` with
   `ASTER_DELEGATION_REQUESTS_ENABLED=1` and fixed model `gpt-5.6-luna`.
   Restart Aster, verify normal health/routes, owner/worker isolation and denials.
   Cleanly replace Companion with the frozen ad-hoc-signed candidate, register
   only the installed app, and launch for Jason's visual acceptance.
4. Coordinate one public/synthetic reviewed question with Jason. Prepare the
   worker before Send: requests expire after four minutes. Activate only the
   existing worker identity for this session. Read its fixed Keychain item once
   via the private bootstrap, allowing the OS prompt up to 90 seconds; no values
   in chat/logs. Use existing subscription auth and medium reasoning, zero tools.
   Bind the resulting job ID/digest to the frozen launcher manifest; all other
   fields and Codex binary must match. No arbitrary queue consumer or retries.
5. Observe metadata-only completion and have Jason read the answer in Companion.
   Immediately disable the worker and independently verify no usable grants.
   After answer acceptance, remove only the new requests drop-in and restart
   Aster to close new submission. This means two planned brief Aster interruptions
   across the experiment. Keep the app installed with submission unavailable;
   preserve ledger evidence. No automatic renewal or unattended worker remains.
6. On failure, stop the worker, remove the new requests drop-in, restore the three
   old modules and whole app, then restart/validate the accepted baseline.
   Preserve failed evidence. Never reset the ledger, delete older checkpoints,
   restore unrelated snapshots or remove the existing owner-readable pilot setup.

No Git push, permission expansion, credential renewal, model change or live
sysadmin action is included. A Keychain/passkey prompt may require Jason's direct
interaction; no password is requested through Codex.

## Acceptance / stop criteria

One explicit submission produces at most one model turn; returned job/digest and
owner match; no tools or attached local context; answer is visible in native UI;
normal chat and authentication still work; worker grants are absent after cleanup;
new submission is closed after acceptance. Collect latency, usage, lifecycle state
and binary/source fingerprints, not raw content. Visual acceptance and live
regression checks are still pending. Failed or ambiguous execution must never be
automatically replayed. Recovery mismatch or additional admitted jobs stops work.

## Resume

Read this gate, the source/artifact manifest and Git status. No deployment or new
credential read has occurred in preparing this candidate. Obtain Jason's explicit
bounded approval before steps 2–6. His interface choice alone is not that approval.

## Frozen candidate validation

28 native tests and 250 backend tests passed. Release build succeeded; the
assembled ad-hoc app passed `codesign --verify --deep --strict`. No app launch,
registration or installation occurred. [Artifact/source manifest](D3-native-request-artifacts-2026-10-08.json)
binds the exact package, four gateway modules/drop-in and worker Python sources.
Artifacts are staged in `/private/tmp/aster-native-request-candidate-20261008`.
Reverify every hash before deployment; missing staging files require rebuilding
and a recorded new manifest, not substitution. Native visual acceptance remains
pending. Local tests do not prove live availability or general reliability.

## Authorization and execution

Jason approved the bounded installation, one supervised native conversation,
private credential bootstrap and cleanup. Execution started after matching source,
artifact, app and gateway hashes; subscription/model/binary configuration remained
identical to the accepted pilot. Worker inactive with zero grants at preflight.

### Installed; waiting before admission

Gateway checkpoint verified and four frozen modules/drop-in installed. Restart
passed: all 43 baseline API paths preserved, three new paths, health 200 and
three unauthenticated denials. Installed main Aster and credentials.py unchanged.
Companion 0.3.0 build 5 installed, signature verified and launched. Whole-app backup
verified at `/Applications/AsterCompanion.pre-codex-20261008.app`; original bundle
also retained at `/Applications/AsterCompanion.native-replaced-20261008.app`.
No earlier backup was removed. No new model call or Keychain read yet.
Worker remains inactive; user asked to prepare a public question and stop at the
review screen before Send. Do not start the four-minute window before readiness.

Prepared metadata-only worker template:
`/private/tmp/aster-native-worker-template-20261008.json`. Compared its base to the
accepted pilot (excluding fictional fixture): exact match, including binary,
subscription authentication, model, reasoning and disabled capabilities. Actual
job ID/digest must replace only assignment fields after user submission.

Resume: wait for readiness, activate the exact worker, coordinate one Send, read
only new job ID/digest from durable envelope, prepare/compare assignment manifest,
run once with supervised bootstrap, and clean up per scope above. If the user
already submitted, inspect expiry/state first; never retry an uncertain run.

### 2026-10-08 — Native sign-in blocker repaired locally

Jason reported the native app stuck on Signing in. Source inspection found
`completion?(await exchangeCode(...))`: optional chaining skips argument evaluation
when the ordinary login caller supplies no completion closure. Thus a successful
web callback can skip token exchange and leave isSigningIn set. This is a verified
source defect consistent with the screenshot; no secret-bearing traffic was
inspected to claim a captured live callback. The prior tests covered refresh but
missed callback-free initial sign-in.

Separated unconditional exchange from optional completion notification, retaining
callback validation, generation guard, PKCE, passkey and persistence policy. Added
synthetic initial-login and failure-notification tests; all 30 native tests pass.
Built and installed 0.3.0 build 6 as the narrow repair requested by Jason.
Signature and installed-file hashes verified; pre-repair build 5 retained at
`/Applications/AsterCompanion.pre-authfix-20261008.app`. Original pre-Codex recovery
copies remain untouched. App reopened; real sign-in acceptance remains pending.
No gateway changes/restart, credential read, worker activation or inference.

[Repair manifest](D3-native-authfix-artifacts-2026-10-08.json) supersedes only the
app portion of the original artifact manifest; gateway and worker hashes remain
unchanged. Stop before request submission until user sign-in/readiness confirmed.

### Native request completed — awaiting owner visibility

Jason reported sending the reviewed request. Read-only ledger reconciliation found
exactly one queued native assignment, with 208 seconds remaining, matching the
owner and fixed model. No resubmission. Actual worker manifest matched the frozen
template in every field except the expected job ID/request digest. Fingerprint:
`63477908bac2dc1f4ef195984134b729bc54ff9f1c1411ded9f8658a0b2fc5b3`.
Activated only the preflight-verified identity and ran the approved worker once.

Job `request-7c942c40-2397-44b9-a020-18dccb18bccb` completed; independent gateway
inspection confirmed completed state, answer digest, usage, no cancellation,
exactly two total jobs (one historical Orion plus this native request), health 200.
Provider usage: 7,823 input tokens, 1,792 cached input, 214 output, 57 reported
reasoning-output, 8,037 total. These are counters, not a subscription invoice.
No raw prompt or answer was read into operator tooling. One inference; no retry.
Private execution evidence: `.aster-local-state/native-request-20261008`.

Immediately disabled the exact worker. Cleanup verified inactivity and zero
nonrevoked grants; Authentik deactivation removed grants before explicit revoke.
No credential renewal, tools, live sysadmin actions or push. Native submission
proves sign-in progressed far enough to authenticate intake, but final answer
visibility is still pending Jason's confirmation. Do not claim D3 graduation.

Resume: have Jason view the answer within the 15-minute memory window. After
confirmation, remove ONLY `aster-delegation-requests.conf`, daemon-reload/restart
Aster under existing approval, verify baseline 43 API paths and healthy normal
service, preserve the completed ledger and native app. Do not restart before
answer acceptance or claim an expired answer remains available. Do not run a
second question under the consumed one-turn authorization.

### Owner acceptance and final cleanup

Jason confirmed "yes, I can see it". This establishes user-reported native answer
visibility for the submitted question. It is not a correctness benchmark or
sysadmin qualification. The callback-free login repair therefore also passed
the real authenticated submission workflow.

After acceptance, removed only the exact requests-enabling drop-in and restarted
Aster as approved. Independent checks: health 200; exactly the original 43 API
paths; new submission routes absent; two completed job records preserved; original
pilot drop-in preserved. Fresh identity query verified worker inactive and zero
access/refresh grants. No further model turn, credential renewal or Git push.
The restart cleared temporary answer text as planned; durable status/digests and
usage remain. Native build 6 and recovery copies remain installed/retained.

## Next Stream A work

This milestone is complete, but D3 remains open. Continue local preparation for
operational usability: explicit disabled/worker-unavailable status, distinguishing
completed-but-expired answer from failed work, reconnect/recovery without duplicate
execution, and a bounded supervised-session start/stop design. Avoid another
fixed Orion test. Follow-up context and completion notifications remain separate
acceptance requirements. Never expand tools or grant sysadmin authority to make
a conversational demonstration appear more useful. A new live session or credential
renewal requires a concrete bounded gate; prior one-turn permission is consumed.
