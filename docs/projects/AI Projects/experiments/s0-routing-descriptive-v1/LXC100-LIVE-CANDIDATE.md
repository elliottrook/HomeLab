# Fixed one-shot candidate — final technical review pending

2026-09-26. Base integrated checkpoint `28a9e49`. Invocation remains disabled.
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

`invoke_once` and the module's command-line invocation unconditionally raise
PermissionError. The internal prepared call path exists for review but is not
called by any enabled public entry. Tests exercise its wiring only with a stub
adapter and stub lifecycle; actual Popen and sockets are mocked in adapter tests.
Enabling invocation requires the next technical review and a deliberate code
change, including refreshed hashes; there is no approval Boolean bypass.

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

## Local validation evidence

8 focused timing/adapter tests and 192 full adaptive tests pass. The focused tests
cover aggregate delayed observations, late readiness, bundle/artifact allowlist
validation, exact direct SSH argv/options, rejected name-only mutation proposals,
canonical guarded-cleanup data, fixed DNS query/target, exclusive prepared-journal
wiring and unconditional public invocation denial. No real network/process adapter
operation was used: Popen/socket were mocked, journal paths were disposable and
the prepared lifecycle was stubbed. Existing integrated tests use only invented
local subprocesses. `git diff --check` passes.
