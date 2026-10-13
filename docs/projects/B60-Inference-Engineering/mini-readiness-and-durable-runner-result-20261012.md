# Mini readiness receipt and durable runner failure records

Received Adaptive `ccc825f0` on 2026-10-12, file
`docs/projects/AI Projects/benchmarks/B60-measurement-response-and-mini-readiness-2026-10-12.md`.
It acknowledges B60 `dd8825f63ef2d47e06bd6a734ffbea8dff658115`, reports
independent revalidation of 11 wrapper and 14 Adaptive answer tests, and names
both response hashes. Recomputed those hashes locally: exact match.
The prior pending acknowledgment/source-pin notes are now historical.

Peer observed Mini account `jelliott`, `/usr/bin/python3` 3.9.6, AC sleep 0,
and successful existing Proxmox/TrueNAS SSH with BatchMode, strict host-key
validation and IdentityAgent=none. This resolves the requested Mini-to-lab
non-interactive transport readiness. It does not establish laptop-to-Mini
administration, installation, restored-production health or a live nightly run.
The peer relayed the lease gaps to the existing platform-owner chat; no need
for Jason to relay them manually. Qualification cases/review custody, actual
Aster-path admission/instrumentation and numeric control limits remain open.

## Concrete concurrent implementation

Reviewed the existing B60 coordinator and fixed a durable-evidence bug:
its recovery exception previously escaped before the final result was written.
Nested finally now saves the terminal result even when release fails, while
preserving the review-required latch, recovery-unconfirmed event, once-only
release attempt and independent host watchdog responsibility. It makes no
success claim and performs no automatic retry. Disk/state-write failure remains
a separate failure that cannot be fixed by claiming a saved result.
SSH calls now explicitly use IdentityAgent=none, matching the verified Mini
access path; authentication and strict host-key checks are unchanged.

Tests cover recovery-loss result persistence, combined experiment/recovery
failure, preparation failure and noninteractive transport options. All 20
historical runner tests pass, including three additional tests; 112 other
focused capture/benchmark tests remain unchanged (132 total).

**DO NOT ENABLE this runner version.** Its evening-window/native-OpenVINO
workflow is still superseded. This is an isolated reliability fix to carry
into the revised shared-lease coordinator, not a deployment bundle, scheduler
activation or new lease contract. No GPU/model/tool call, production/service/
schedule change, download or new credential occurred.

Next: platform owner must publish the bounded receipt/expiry/recovery interface
and reviewed staging path. B60 can then implement/test its consumer without
inventing competing reservation authority. Adaptive should complete independent
case/reviewer custody and the isolated full-path harness concurrently. Continue
non-disruptive preparation immediately, not only inside the exclusive window.
