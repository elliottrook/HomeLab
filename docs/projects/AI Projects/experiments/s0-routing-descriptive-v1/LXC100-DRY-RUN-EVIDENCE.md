# Full feasibility flow — injected fake transport only

Status: candidate awaiting technical review before local commit or any user run
approval. Base1e506bd contains reviewed plan/supervisor. No real transport branch
exists; no SSH, DNS request, unit/namespace/container, file mutation on LXC100 or
accepted-corpus access occurred in this step.

## Implemented contract

`s0_probe_state.py` consumes a concrete FakeTransport with invented response bytes.
No callbacks, arbitrary transport subclass, command strings or path arguments are
accepted by the execution boundary. real_transport unconditionally raises even if
an approval flag is supplied. This is not protection against a programmer editing
Python; it is an intentionally non-executable remote candidate.

Order: exact raw LoadState preflight -> absent-path preflight -> health/headroom ->
two DNS checks -> exclusive create -> start/ownership -> running controls/denials ->
worker result -> postflight health/DNS -> stop owned unit -> inspect cleanup ->
remove owned canary -> verify absence -> final health/DNS. No next step can turn
an earlier failure into a pass. No restart, repair or automatic retry operation.

LoadState requires exact bytes, successful integer exit status and empty stderr.
Other invented transport observations use bounded exact JSON schemas; future real
observation collectors are not implemented or claimed tested. Health verifies a
running guest, running healthy Pi-hole, consistent container identity/status/restart
inventory, guest available-memory and cgroup headroom, and low memory pressure.
Postflight and final service baselines must match; all DNS responses must meet the
same success/2s criteria. Latency changes are not scored as routing quality.

DNS parser checks the fixed example.org A-question, transaction ID, response bit,
opcode, truncation, error flags and question bytes in two bounded synthetic packets.
It emits no DNS answers or raw packets into evidence. No live DNS packet is sent.

Running inspection requires exact proposed property types/values, kernel cgroup
limits, expected invocation identity, ready phase and all denial checks true.
Missing/unsupported properties fail. This validates the fake contract, not actual
systemd property conversion or enforcement. Result must be done, successful and
bound to the same invocation. Every command/stream has an8KiB bound; total input
observations64KiB; final evidence8KiB. Raw output/errors are not echoed, only bounded
operation states and SHA256 response references. Evidence is returned in memory;
no atomic/persistent output store is claimed by this module.

## Failure and cleanup semantics

If preflight fails, no create/run/stop/delete occurs: existing unit/path might belong
to someone else. After any create attempt, postflight and cleanup inspection still
run. Partial/uncertain creation does not establish ownership: preserve for manual
recovery, do not delete. Uncertain start has a manual-unit-recovery-required outcome;
never stop a unit solely because its name matches. Verified own invocation may be
stopped even after a failure. Failure to stop is retained, not hidden by later absence.

Removal requires confirmed creation, ownership, exact directory/file modes and
canary content, no extra entries, and verified unit/cgroup absence. Any failed guard
prevents removal; verification/final health still occur. Unexpected /usr denial-probe
artifact also fails final cleanup verification. No wildcard cleanup or unrelated
service restart exists. Failed/malformed/timeout/missing observations remain failure
or inconclusive, even when cleanup eventually succeeds.

A real implementation must establish ownership from exclusive creation receipts and
runtime invocation identity. The literal fixture identity is not an authentication
scheme. No real adapter can be plugged in without new reviewed code and scope.

## Verification

17 new state-machine tests and161 complete adaptive tests pass. Failure injection
covers every operation; pre-existing paths/unit; failed command/stderr/oversize;
invalid DNS identity/question/rcode/latency; headroom/pressure failures; postflight
service restart; uncertain creation/start; every isolation property and denial check;
changed invocation; all cleanup guards; missing final absence; bounded non-secret
output; duplicate JSON and unsupported operations. The exact all-success order is
asserted. Core execution is tested with sockets, subprocess and file opening denied.
No invented successful fixture response is recorded as a HomeLab observation.

## Next gate

Technical review of this dry-run candidate before local commit. Then present a
concrete shared-host mutation proposal; do not silently add or enable real transport.
Actual health/DNS collectors, remote supervision/ownership recovery and OS controls
remain unverified until explicitly authorized fixture-only execution. Accepted-data
evaluation remains separately prohibited. No install, deployment, permission change
or push authorized. Rollback is removing unused local candidate code; live state is
unchanged.
