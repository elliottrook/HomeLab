# F2 diagnostic candidate — Stream A independent review

**Evidence class:** offline source and synthetic tests, October 18, 2026.
**Decision:** suitable for a separately reviewed *disabled* target-Linux
installation candidate; F2 remains FAILED/UNKNOWN for October 17. This is
not an installation, archive result, receipt, or drill admission.

The platform owner prepared local commit `49f81490` and
`services/local-ai-lease/F2-DIAGNOSTIC-DISABLED-RELEASE-CARD-20261018.md`.
Stream A read the guard and focused test source in the platform checkout,
recomputed SHA-256 values `6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f`
and `1582fb7ffc9ed3a851ce0346cc0fc727a6550759e3537c261eabd1c60c2459d6`,
and ran the focused 14-test suite independently; all 14 passed.

The guard reports only `preflight`, `observer`, or `result` on failure. It
does not include command output, archive paths, exception text or private
source content. The new one-denial-per-gate synthetic matrix confirms no
observer child starts when each preflight gate fails. Existing tests cover
deadline termination, result-shape refusal and the absence of an admission
receipt. These are source-level checks on macOS, not installed-path proof.

The diagnostic phase is intentionally coarse. A future `preflight` result
will not name the failed predicate, and an `observer` result will not say
whether the archive probe started. No October 17 phase was recorded, so this
candidate cannot reconstruct that attempt or distinguish archive corruption
from another denial. The tests use fictional input; they do not measure the
43.6 GB LXC110 archive or its completion time.

Next, the platform owner should validate the pinned candidate and rollback on
target Linux with timers and effects disabled, under a bounded host-change
approval. Only after that review may Jason approve one fresh-cycle,
supervised, read-only scan. Complete exit-0 results for 104, 110 and 116
within the outer deadline are required to close F2. F3 receipt release and a
full-stop drill remain separate later decisions.
