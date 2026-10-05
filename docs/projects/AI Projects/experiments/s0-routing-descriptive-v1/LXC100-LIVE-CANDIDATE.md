# Fixed approval-gated one-shot — released for coordinating invocation

2026-09-26. Prior reviewed invocation-disabled checkpoint `d476158`; integrated base `28a9e49`.
Invocation requires the fixed released approval record. Last preflight review passed;
the coordinating task confirmed the exclusive window for this single probe.
This preparation task has not invoked it.
No SSH, live DNS, LXC100 modification, accepted-corpus evaluation or push occurred.

## Inspection timing

The constant worker now waits ten seconds after readiness, inside unchanged
RuntimeMaxSec=15. All unit-properties, cgroup and canary queries share one deadline
at the parent's pre-spawn monotonic start plus eight seconds. Each command gets
only the remaining budget; every return is checked against the same deadline.
Thus timely completion has at least two seconds before normal readiness-window
expiry. Slow SSH/readiness consumes the budget rather than extending it. Late
responses fail closed with the existing manual-recovery path. Runtime enforcement
itself remains unverified on LXC100; startup failures/timeouts remain inconclusive.

Fake-clock tests cover successful delayed collectors, expired readiness, a first
late response, second query consuming the budget, and third query finishing exactly
at the deadline. The complete lifecycle also uses this function, with bounded
FixedSession stream handling and process cleanup.

## Prepared fixed adapter

`s0_live_candidate.py` implements direct `/usr/bin/ssh` process creation with the
exact catalog argv, isolated fixed environment, no stdin, bounded session pipes,
new process group, no shell wrapper and no generic operation/path argument.
Only lifecycle operations are accepted. Historical name-only stop, reset and
remove proposals are explicitly rejected. Receipt-guarded cleanup accepts only
canonical bounded ownership data and the exact constant source.

The DNS adapter connects UDP only to `192.168.20.20:53`, uses a two-second timeout,
accepts only the fixed example.org A query and caps receipt at 513 bytes. The
existing collector rejects packets larger than 512 bytes or inconsistent peers
and validates response flags/question. Two queries remain the fixed count.

The prepared one-shot call requires an externally supplied reviewed SHA256 of
`lxc100-live-candidate-manifest.json`. It validates the exact artifact allowlist,
every source/parser/test/plan hash, prior integrated manifest hash and catalog
before creating a journal; verification repeats before each external operation.
This detects ordinary file drift but is not protection against a malicious local
owner replacing trusted code between checks. Pins are review provenance, not
cryptographic authorization or a substitute for human authority.

The local journal path is fixed:
`/private/tmp/aster-s0-lxc100-one-shot-20260926`.
It must be newly created exclusively; an existing path/partial attempt blocks a
rerun. Its first record pins the reviewed manifest and command catalog. Recovery
is the existing read-only journal inspection; no retry, stop or delete is inferred
from prior approval or apparent absence. No journal at this path was created by
tests: they used injected temporary paths and stub adapters only.

`invoke_once()` now accepts no arguments and rejects every CLI argument. It reads
only the fixed external `lxc100-approval-record.json`, validates exact fixture scope
and conveyed conditional human authorization, requires passed technical review,
confirmed exclusive operator window and explicit one-shot release, then verifies
the recorded manifest hash before the prepared lifecycle. The released record
marks technical review passed, the exclusive operator window confirmed for this
one coordinated probe, and one-shot execution released under Jason's conveyed
conditional authorization. Invocation is reserved to the coordinating task. The record is
outside the manifest artifact set: code/plan are pinned first, then approval binds
the final manifest hash. It is provenance, not cryptographic identity proof.

Manifest, artifact and approval reads now traverse path components using
O_NOFOLLOW, open the final file nonblocking with O_NOFOLLOW, require regular files,
current effective-user ownership, one link, no group/other writes and bounded
size. Content is read and hashed from that descriptor; before/after descriptor
metadata and length must agree. Symlink/path-swap, in-place change and special-file
fixtures are rejected. This removes the earlier check-then-open symlink race; it
does not protect against a malicious trusted owner rewriting code and provenance.

## Remaining risk before invocation

The preceding integrated risk statement still applies: confinement/actual systemd
output is UNKNOWN; an uncertain remote outcome is not proof of termination; no
name-only stop is attempted; root replacement races require an exclusive operator
window; partial creation/cleanup may need manual receipt-based recovery. The
longer ten-second wait remains within the original 15-second bounded unit life and
does not raise CPU/memory/process/network permissions. Strict format mismatches or
insufficient timing budget yield an inconclusive result, never an automatic retry.

A pass would establish only this fixture's feasibility. It cannot authorize
accepted-corpus evaluation, install packages, alter other infrastructure or push.

## Previous checkpoint validation

At `d476158`, 8 focused timing/adapter tests and 192 full adaptive tests pass. The focused tests
cover aggregate delayed observations, late readiness, bundle/artifact allowlist
validation, exact direct SSH argv/options, rejected name-only mutation proposals,
canonical guarded-cleanup data, fixed DNS query/target, exclusive prepared-journal
wiring and unconditional public invocation denial. No real network/process adapter
operation was used: Popen/socket were mocked, journal paths were disposable and
the prepared lifecycle was stubbed. Existing integrated tests use only invented
local subprocesses. `git diff --check` passes.

## Final authority hardening validation

The authority/read test suite adds temporary-file coverage for regular ownership,
size/mode, final/intermediate symlinks, hardlinks, FIFO, mutation during read and
path replacement after open. Temporary approval records and stub prepared calls
exercise released scope, pending release, mismatched scope/provenance/pin,
arguments, duplicate keys and missing records. No actual lifecycle/network call
is used. The released repository approval is bound to this manifest and its test calls
only a mocked `_prepared_one_shot`, even when release validation succeeds.

Final local validation: 8 authority/read tests, 16 combined timing/adapter/authority
tests and 200 full adaptive tests pass. All external adapters were mocked; no
network or production mutation occurred. Source/manifest/approval pins were
regenerated after the final edits. Release validation is exercised with execution mocked; the actual probe has not
been invoked by this preparation task.

## Release provenance — 2026-09-26

The coordinating task independently reproduced 8 authority/read and 200 full tests
and verified every artifact of pending-gate manifest
`71ab5e6ef00d779e4cc3401c051e4ad9ab4a34df7b5d3b3aa4d8db397c21c6df`.
It passed the last preflight review, confirmed the exclusive operator window for
this single probe and instructed release under Jason's conditional approval.
The pending-gate checkpoint is `eb1deef`. This revision changes only release
provenance/documentation, the real-record test (mocked execution) and corresponding
hashes; it does not expand probe scope or permissions. After regeneration, the
external approval record binds the new final manifest. The coordinating task will
perform its final hash/preflight check before the authorized one-shot. No invocation
or remote Git synchronization is performed by this preparation step.
