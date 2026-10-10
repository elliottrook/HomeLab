# LXC100 attempt 2 — technically reviewed, fresh approval recorded

2026-09-26. Run-001 evidence commit `ab34738`. No automatic retry is authorized.

## Why a distinct attempt

Run 001 failed in read-only health preflight. Its five-record chain proves no
mutation intent; its original journal remains untouched. The coordinating task
reported a changed Docker inventory and guest-root memory.max=`max`. These were
invalid collector assumptions, not proof of guest/isolation failure. The exact
stderr is unavailable; do not pretend to identify the failing assertion uniquely.

This candidate uses a new exclusive journal
`/private/tmp/aster-s0-lxc100-attempt-2-20260926`, new manifest
`lxc100-attempt-2-manifest.json` and new external approval identity
`lxc100-attempt-2-approval.json`. Jason separately replied `approve` after the corrected run002 scope was presented
in the coordinating task. This fresh approval covers exactly one run002 fixture;
it is not a reuse of run001's approval. Technical review passed. Execution remains
gated until this final revision is hash-bound in the external approval record;
release preparation itself does not invoke the probe. The original files and run-001 journal are preserved.

Remote unit/canary names stay unchanged only because pinned run-001 evidence
proves no mutation was attempted. The launcher additionally validates that chain
before any prepared invocation. The new attempt still requires current exact
unit-not-found and absent-path preflights; history never substitutes for live state.
Any uncertainty fails closed. No preparation-stage SSH, DNS or LXC action occurs.

## Changed health contract

The fixed Docker collector discovers 1–32 unique container names, validates each
against a bounded name grammar and inspects only running/state/health/restart
metadata. It has the existing shared 12-second subprocess deadline and 4 KiB
per-command output cap, within an 8 KiB outer result limit. Overflow, malformed
names, duplicate inventory, missing Pi-hole or unexpected fields fail closed.

Existing inactive containers are permitted only in stable exited/created states;
they remain part of the exact baseline. Their existence must not be mistaken for
a newly failed service. Active containers must be running and healthy/healthless;
restarting/paused/removing/dead states are rejected. Pi-hole must be running and
healthy. No claim is made about the currently observed state of the additional
`code-server-pre-authentik` container; its state is UNKNOWN until a new preflight.
Before/after/final inventory, running/state/health/restart values must match exactly.
A new/removed container, state transition or restart therefore fails the gate.
This detects change, not whether the pre-existing inventory is architecturally ideal.

The fixed host-side command is direct SSH to `192.168.50.10` carrying only
`pct status 100 --verbose`. Its bounded parser requires running status and integer
maxmem/mem/maxswap/swap fields; duplicate, missing, unknown or malformed fields
fail closed. Optional known numeric metadata is validated then discarded.
Actual verbose output variations remain UNKNOWN; no permissive parsing fallback.
Host memory headroom must be at least 256 MiB; swap use must remain zero. Configured
host memory/swap limits must match the initial baseline throughout the attempt.
Ordinary changing current memory use is observed, not required to be identical.

Guest LXCFS MemAvailable must remain at least 512 MiB, no greater than MemTotal;
MemTotal cannot exceed host maxmem. Guest memory PSI some avg10 must remain below1.
The collector no longer interprets guest-root memory.max or memory.current as the
LXC's configured allocation. Unit-specific memory.max=64 MiB, memory.swap.max=0,
pids.max=1 and all existing unit isolation checks remain unchanged. The ten-second
readiness window/eight-second shared inspection deadline and 15-second unit limit
remain unchanged. No additional machine, installation, permissions or cloud use.

Host/guest resource observations are retained as bounded non-secret journal records.
The services and configured limits form the exact before/after/final baseline.
This is a read-only accounting change, not a modification of LXC resource settings.

## Risk, rollback and stop conditions

This remains a one-shot root-transport feasibility check on a shared household
host. More discovered containers cause more bounded read-only inspections; the
shared deadline prevents unlimited inventory cost. Concurrent service maintenance
would cause a baseline mismatch, so an exclusive operator window must be confirmed
anew. Nested systemd confinement and actual output formats are still unproven.
Unknown start/termination or partial canary cleanup remains manual recovery; no
name-only stop/delete, generic command, automatic retry or journal reuse is allowed.
Original 64 MiB/one task/10% CPU/15-second limits, no network/secret/corpus access,
receipt-guarded cleanup and local kill/reap behavior are retained. Failure before
mutation needs no remote rollback; later ambiguity retains receipts for human
verification. No infrastructure changes outside the single fixture are permitted.

## Acceptance and evidence

A useful pass requires fresh absent-state preflight, valid dynamic baseline,
host/guest resource gates, exact denial/property checks, verified completion,
receipt-guarded cleanup and matching final service state. A failure is inconclusive,
not evidence that accepted-corpus execution is safe. No model or corpus evaluation
is permitted. Local tests use invented collector/lifecycle fixtures, local child programs and
mocked sockets, plus the sanitized real host-status capture as a parser regression. The recorded fresh attempt2 approval is separate from run001.

## Fresh authorization and release scope

Jason's separately recorded `approve` authorizes exactly one corrected fixture-only
run002 on LXC100, with a fresh exclusive journal, bounded dynamic inventory and
host-side memory/swap checks, unchanged 64 MiB/one-task/15-second limits and no
automatic retry. Technical review passed; the coordinating task confirmed the
exclusive operator window for this single probe. Preparation ends with an external
record bound to the final manifest; no invocation occurs while preparing it.
The probe remains on the shared Docker/Pi-hole guest. An uncertain outcome may
require manual receipt-based cleanup within the reviewed bounds. No package
installation, unrelated change, accepted-corpus evaluation or push is included.
The provenance is a record of conveyed human approval, not cryptographic identity.

## Local validation checkpoint

208 full adaptive tests pass, including eight focused attempt2 tests with malformed
host accounting, headroom/swap pressure, dynamic stable stopped inventory,
add/remove/restart/state/configuration baseline changes, inventory/name bounds,
guest PSI pressure, no guest-root memory-limit dependency and distinct unapproved
attempt identity. Existing complete lifecycle failures now include host-lxc-status.
The full captured-output regression uses real sanitized diagnostic stdout supplied
by the coordinating task. Other collector/lifecycle fixtures use invented data,
local child programs or mocked adapters. Release-record execution is tested only
with the prepared lifecycle mocked. Source pins and final approval binding are
verified after artifacts settle; no attempt2 journal or remote object is created
during preparation. Technical review and fresh human approval have both passed.

## Captured-output parser correction — reviewed

The coordinating task provided the complete sanitized `pct status 100 --verbose`
diagnosis output. It is retained unchanged in
`fixtures/pct-status-100-run001-diagnosis.txt`, with its bytes pinned in the attempt2
manifest. A regression asserts exactly the five expected required resource values.
The parser now requires vmid exactly100 and type exactlylxc, accepts only the six
known finite nonnegative pressure fields, bounded ASCII name/tags and known numeric
metadata. Count fields are bounded nonnegative integers (pid/cpus positive).
Unknown fields, duplicate fields, invalid identity, nonfinite/negative pressure,
invalid tag/name grammar and resource failures remain rejected. No new network
query was made to obtain this fixture; its source is the coordinating-task capture.
Fresh human approval is recorded in RUN-002-AUTHORIZATION.md. The coordinating
task independently reproduced eight focused and208 full tests and passed technical
review. The final external record must bind this settled revision before invocation.

## Run 002 outcome — one-shot consumed

The coordinating task verified manifest
`1713058f4f280e116933295ec633f5c59925f8a9cba1635dae9a371ea0e322b2`
and invoked it exactly once. The result was `failed-or-inconclusive` during
preflight. Unit-state, path, guest-health and host-LXC-status collection completed,
followed by a bounded resource observation. The terminal record states
`mutation_attempted=false` and `manual_recovery_required=false`; there was no
create/run intent, canary, remote stop or corpus evaluation.

The exact cause is **UNKNOWN / REQUIRES VERIFICATION** because exception text is
intentionally omitted from the bounded journal. A separate fixed two-query DNS
diagnostic succeeded after the run, which proves current reachability but does not
identify the earlier failure. The approval record is now marked consumed and the
exclusive journal prevents reuse. No retry is authorized. Exact invocation bytes,
journal records and provenance are preserved under `run-002/`.
