# Stream A candidate-H admission inactive installation

**Date:** 2026-10-25  
**Decision:** inactive source compatibility **PASS**; live evaluation remains **NO-GO**

Jason approved the platform-owned four-file inactive installation after
independent review of local commit `f109c1f0`. The review confirmed explicit
rejection above the 16 KiB artifact bound and exact accepted F5 binary, unit
and authentication identities.

The installed admission library, lease contract, adapter and entrypoint match
the four hashes in
`services/local-ai-lease/STREAM-A-EVALUATION-ADMISSION-CANDIDATE-H-INACTIVE-INSTALL-CARD-20261025.md`.
All are root-owned regular mode-`0644` files with one link. The three replaced
files are preserved byte-for-byte in the root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/stream-a-admission-f109c1f0-20261025`;
the checkpoint also records that the admission library was absent beforehand.

Installed-path imports passed. The target-Linux admission, lease, adapter,
entrypoint and watchdog suites passed 69/69. The real inert-wrapper regression
passed separately after constructing its required repository-shaped temporary
fixture. The first test command omitted fixture source files and failed in
test setup before exercising the candidate; it caused no host effect and the
corrected fixture passed 1/1. The unchanged wrapper returned only
`effects=disabled,state=source-only`.

Postchecks found both evaluation recovery timers disabled/inactive and no
lease, lease lock, operation lock, F5 observation, admission artifact,
evaluation process or candidate-H workload. No consumer, schedule or model
state changed.

This result does not create F4/F5 evidence, arm recovery, acquire a lease,
stop a service or authorize either model workload. The next serial dependency
is tonight's scheduled F2 outcome; only a complete three-row result can admit
the separately reviewed F3/F4/F5 production chain.
