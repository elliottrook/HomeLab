# D4 candidate-g release-manifest pin install — 2026-11-04

## Decision

**PASS; INSTALLED INACTIVE.**

The exact one-file platform correction is now installed with its predecessor
retained under root-only custody. Candidate manifest digest is
`4d8e7db2…2b92`; installed custody is `root:root 0644` and checkpoint custody
is `root:root 0700`.

The target focused suite passed 22/22. The actual installed reserved-runner
manifest verifier—which the earlier static preflight omitted—successfully
validated all 34 installed pins and returned the corrected EPUB source and
validator hashes. Lease and shared-state gates remained clean. No booking,
service restart, model request or workload occurred.

This closes the deterministic claim-time defect. It does not retry either
spent booking. A fresh candidate-g booking still needs an exact current ledger
check and the retained service-stop/start decision.
