# Preparation checkpoint — 2026-10-12 evening

Preparation-only heartbeat; no model/GPU/network endpoint calls, downloads,
mounts, lease acquisition, timer/service change or production mutation.
Fetched authoritative main and all three project branches. Peer branches have
not advanced since the preceding receipt; no repeated request or wait message
is required. This packet contains one additional actual reliability fix.

Exact branch/path receipts (SHA-256 over Git file bytes):

- Adaptive `aa1d6dc9839e43b2e36e1cb05793abc38014cc19`,
  `docs/projects/AI Projects/benchmarks/B60-coordination-interface-2026-10-12.md`,
  `d2d23f829bb8f669ff80e43c8942a5f4ed348f9aa30549ca7c4ea8f9e9bd059f`.
- Platform `fc60e5a2c9eac8f311ce8e6c0a83b901fe55600b`,
  `docs/projects/Local-AI-Platform-Split.md`,
  `358f1176d792c0e88b32ad65903a2384fa8de44904e3f839f27a2978b9f4c7be`.
- B60 `58a898e499c9236b354555764182f40f1ee17257`,
  `docs/projects/B60-Inference-Engineering/adaptive-v2-baseline-receipt-20261012.md`,
  `0c5ae4ff581b285b13f9a12b5320b7c01b095bbfdd808939702e4f6537354427`.

## Durable status-write fix

The undeployed coordinator's fixed `status.json.tmp` filename used exclusive
creation. A process interrupted before rename could leave that file and block
every later status update, including recovery evidence. It now uses private
unique same-directory temporary files, fsyncs file data, atomically replaces
the target and fsyncs its directory. Cleanup removes only the temporary file
created by that invocation; stale/unrelated files are preserved. Nonfinite
JSON is rejected before file creation. A failed replace preserves prior state.
Disk failure still propagates; this change cannot promise evidence persistence
when the filesystem fails or make the runner safe to deploy.

Three added offline tests cover stale-file survival/nonblocking updates,
failed replace cleanup/prior-state preservation and nonfinite JSON rejection.
Focused handoff validation passes 16 coordinator, 58 B60 integration and 14
Adaptive answer tests (88 total). This differs from the full implementation
checkout's prior 142 tests; do not add these counts or claim a new full-suite run.

## Publication and resume boundary

This fix lives in the writable focused handoff checkout under `/private/tmp`.
The full implementation checkout currently has read-only workspace permission;
it has not been edited or synchronized with this successor. The Git-tracked
coordination branch is the durable recovery source. On a later writable full
checkout, integrate the exact coordinator/test diff, run its full suite and
record the import rather than assuming both checkouts contain identical code.

DO NOT ENABLE the historical evening/OpenVINO coordinator. Shared-platform
receipt/expiry/watchdog, consumer exclusion, exact recovery and reviewed model
staging remain external prerequisites. Adaptive's full-path admission/clock,
protected evidence backup, quality/sample policy and per-class original-9B
useful-answer limits remain open. Consume an actual owner-published interface
before implementing live admission; do not invent a second lease contract.
Resume at the next preparation check-in, fetching all branch tips first. No
human approval is missing for the safe work completed here and no background
experiment is claimed to be running.
