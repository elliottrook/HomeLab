# Exclusive entry-controller wiring — 2026-10-29

Status: separate controller installed; first restore-only qualification
scheduled and independently verified for October30 at03:10 America/Vancouver.
The live qualification has not happened. This is not an accepted unattended
AI-stack recovery proof and not a model result.

Jason's current Stream A authorization covers the project through completion,
in-scope model changes during actual bookings, and non-exclusive work outside
bookings. No repeated model-by-model conversational approval is needed. The
controller must restore the verified actual entry stack, not assume that every
entry is the historical accepted 9B configuration. Failure of an engineering
gate remains a stop; it is not a request for another general approval.

## Implemented candidate

- Combined booking claim, existing shared host exclusion, canonical durable
  lease/operation markers, private guest-local file checkpoints and unit state.
- Exact source-pinned CLI: launch/run/watch/recover plus static validation.
  The independent host watchdog has a separate systemd service, exact owner
  cgroup fencing, no restart, and a bounded lifetime. No chat/Mini connection
  is required by that design; live integration is not yet proven.
- Owner loss before a claim aborts without restoring a snapshot over another
  owner. Partial durable claim/binding writes are reconciled against the real
  ledger and both canonical markers. Unknown ownership is never deleted.
- Admission reuses the platform's current-cycle retained archive integrity
  verifier, exact TrueNAS task/mirror metadata, and whole Proxmox backup-job
  proof. It also checks booking timing, xe/e211/render-node identity, resource
  headroom, plan pins, actual timer triggers, control plane and source-local
  authentication. No task-success flag substitutes for archive integrity.
- Actual source-local process projection binds the model and executable to
  the active llama unit. Raw argv/environment and configuration contents are
  never returned to the agent or coordination branch.
- News ingest/digest services and the News UI now join the two News timers in
  the declared drain, alongside Aster, Speech, EPUB and Paperless. Timers stop
  before triggered workers; backend stops last. All callers are quiesced again
  on recovery re-entry before configuration restoration.
- Calendar timers clear persistent missed-run timestamps before rearm. This
  deliberately skips missed events, not claims successful application work.
  A separate harmless real systemd fixture proved both positive catch-up and
  no replay after `systemctl clean --what=state`; no application timer was
  changed in that fixture. Monotonic/boot timers remain unsupported.
- Trial failure and restoration success are separate. A failed/uncertain trial
  finishes the booking as failed-restored, never green merely for recovery.

## Validation and actual source receipts

Local:123 Lab Hours tests,5 dormant-installer tests and70 existing full-inference
regression tests. Proxmox:109 final focused tests passed against the installed
dependency set plus the standalone preparation/scheduler sources. Tests use
fake stack effects and real disposable files/processes. They do not qualify
live AI restoration. A separate real systemd sleep-service fixture also passed
actual owner observation, exact cgroup fencing and fixture cleanup; no AI unit
was involved.

Dormant host staging: `/root/b60-exclusive-wiring-20261029.WsPURv`.
Dormant probe helpers: `/root/b60-exclusive-probe-20261029.WsPURv` in guests
104/110/114/115/116. The installed controller is separately at
`/usr/local/libexec/local-ai-lease/exclusive-session`; four root-only helper
files are installed at `/usr/local/libexec/local-ai-lease/entry-checkpoint` in
the five guests. Private metadata-only plans and the first protected activation
profile were prepared. No running AI service, model, GPU workload, lease,
existing production stack configuration or application timer was changed.

Installation initially refused Mac UID501 and AppleDouble archive entries.
Both were transport metadata defects, not a reason to weaken custody checks.
The preserved failed candidates remain under the staging root; clean extraction
used `COPYFILE_DISABLE=1` at packaging and `tar --no-same-owner` on Linux.
Only the task-created top staging directory's owner was corrected explicitly.
No old platform file was overwritten. Static validation's formerly hard-coded
`armed:false` was corrected to `activation_not_inspected:true`, with exact
old/new hashes and rollback copies at
`/var/lib/local-ai-lab/exclusive-status-correction-20261029`.

The first real inventory probe failed closed with `ARTIFACT_SCOPE` on guest110.
Its accepted GGUF resolves to
`/usr/share/ollama/.ollama/models/blobs/sha256-cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`.
The fix permits that narrow blob directory, not all `/usr`; an offline
regression rejects unrelated `/usr/share` artifacts. The runtime projection is
`/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server`.

All five subsequent probes passed, reading metadata only:

| Guest | Declared configuration files | Plan SHA-256 |
|---|---:|---|
|104|12|`69c8408bd0191a8ab3c85882a81378a2224d00391029cc15f489f17849c4aa08`|
|110|2|`71aa5f835b90f6ce2e506882e14837ad583b7c905e10ef3b2e78f5424ca0f122`|
|114|7|`a96363f469cdf25ed50067cd90e4ab37722f83f19d04a56e6fa5d7178a157413`|
|115|3|`8b1aed9f7feba2d537fb48253a508f2004950c03258b2b0db9e69cfeea303a86`|
|116|4|`6c53f7b2e4f36838e1e7d2597270056bc05d62b229de121442a27d80945e8075`|

This includes unit fragments, drop-ins and all repeated EnvironmentFiles
paths, not their contents. The root-level `/etc/aster-llama.env` is an exact
file exception, not a grant to checkpoint arbitrary `/etc`. Extended metadata
such as ACL/xattrs is currently refused rather than silently lost.

## Installed receipts and actual first schedule

All30 installed controller dependency pins match the reproducible v4 source
bundle. SHA-256 of canonical sorted compact JSON over the pin dictionary is
`f5085fbb7b7e8e456be6ac6157867a1af8e808a2e139fb64c03caeb991d25e85`.
The v4 build descriptor SHA-256 is
`ce2ed7f7165160277eb627e496077adfd8c8fe6d476b62a2d888429f76d10ab4`.
That descriptor describes a generated artifact, not live arming state.

| Installed path | SHA-256 |
|---|---|
|`exclusive-activations/b60-exclusive-20261030.json` under `/var/lib/local-ai-lab`|`a69b57d3a3764aa67819571b702622d5b238166db40622f1a9cca0d4bd3955af`|
|`/usr/local/libexec/local-ai-lease/b60-exclusive-integrity/lab_hours_exclusive_integrity_prepare.py`|`af8e054b2032c80f3d27f95bee0e603ef34aefa9cb05ce2f0c60c4460fd85c01`|
|`/etc/systemd/system/b60-exclusive-integrity-20261030.service`|`6313e65ebcde2196ce83df215be053dbb6a4dc5cad11b6b36a7ea504d89c334a`|
|`/etc/systemd/system/b60-exclusive-integrity-20261030.timer`|`8ef8ef39f456bbad338d9cfd9ff73439f45bb06ccca00c6409204cd145766f2b`|
|`/etc/systemd/system/b60-exclusive-qualification-20261030.service`|`4c3fd7de312ac1adc6548adc0ca09b12051244678328f6882fc78535b94c9f9b`|
|`/etc/systemd/system/b60-exclusive-qualification-20261030.timer`|`3b9d4d33c033d95a8d7b7296f421b7b55f505866c9d725916e12a12117d05cc9`|

Both timers were independently observed `active`/`enabled`, with empty
LastTriggerUSec and the exact next times October30 at01:15 and03:10 PDT
(08:15/10:10UTC). Both corresponding services were inactive,MainPID0.
The shared lease remained `ready`; no experiment or current claim existed.
These are future non-persistent one-shots, not30 repeated9B smoke tests.

The01:15 preparation checks the completed whole Proxmox backup and the first
same-night TrueNAS pull, then performs/reuses bounded low-priority retained
archive integrity. It yields to known maintenance, competing backup IO and
source drift. It preserves a valid peer receipt and keeps previous metadata
when refreshing a prior-day receipt. It must finish by01:40 and never changes
the AI stack. The later03:10 admission independently rechecks all three fresh
TrueNAS pulls and the exact LXC110 mirror; a preparation success alone grants
no lease. The previously observed F2/F3 clocks were October29-only, so this
new exact-night producer closes that scheduling gap without reusing stale proof.

The03:10 transaction captures the actual entry, arms the independent Proxmox
guardian, claims the existing booking, drains the declared stack, executes no
model candidate, then restores/verifies the entry and releases. Trial cutoff
is03:15; restoration deadline is03:55, with the existing reservation buffer
through04:10 and the strict04:15 external boundary unchanged. No35B or full-path
benchmark is scheduled. This qualification is necessary implementation work,
not the expanded programme's deliverable.

## Remaining work and exact next action

The next live dependency is the actual booked window, not human authorization.
Do not invoke the stack transaction early or start a duplicate experiment.

1. After the scheduled times, read sanitized terminal/status receipts under
   `/var/lib/local-ai-lab/exclusive-integrity/b60-exclusive-20261030/` and
   `/var/lib/local-ai-lab/exclusive-sessions/b60-exclusive-20261030/`, plus the
   authoritative booking and guardian/owner unit state. Never export the raw
   guest-local configuration checkpoints.
2. Verify fresh archive/mirror admission, exact entry restoration, terminal
   booking state, all previously active schedules, no missed-job replay and
   absence of the exact candidate/owner. A passed fixture or launch is not this
   receipt. On failure retain custody/state, record the exact cause and recover
   safely; never automatically retry a GPU/device failure or clear locks to
   make health green.
3. If normal qualification passes, prepare a separately bounded actual
   owner-loss qualification in a later existing booking. No model approval is
   needed, but do not claim that exercise has already run or is scheduled.
4. Only after independent restoration proof, extend the activation schema to a
   reviewed candidate workload and declared mount/resource recovery. The first
   candidate screen remains the staged35B reasoning-on model, not another9B
   diagnostic relabelled as the deliverable.
5. Continue source preparation safely outside exclusive use. Keep Adaptive's
   task/scorer/quality/latency decisions separate from hardware measurement;
   no numeric release bar, held-out review or complete-answer result is created
   by these tests. Integrate the new receipt namespace into monitoring before
   graduation; existing Lab Hours Doctor still detects stale claims/service
   downtime but does not yet report this namespace as its latest success.

The first activation profile intentionally permits only restore qualification.
It is a technical release gate, not a new human approval requirement. Arbitrary
mount/device changes, other runtime identity adapters, inactive-backend entry,
new undeclared mutation paths and extended metadata are not yet supported.
This limitation means the general model-testing controller is not yet qualified
for arbitrary changes. Do not mark the programme complete or pause its existing
continuation automations. The first scheduled qualification now has an actual
independent host executor; results still depend on that host and all fresh gates.
