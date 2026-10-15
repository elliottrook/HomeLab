# D4 offline incident-plan boundary

Status: **offline candidate; no connected observation or permission granted**.

The SA1/SA2 incident recorder previously accepted an observation whenever its
target and kind appeared in the global read-only catalogue, even if that pair
was absent from the incident's observation plan. Repeated observations of one
planned pair could also exhaust the four-observation budget. If evidence for a
later step arrived first, subsequently receiving the earlier step left the
cursor pointing at the already-filled later step.

Local commit `dd612eb8` bounds each accepted observation to an unfilled
target/kind slot in that incident's plan and recomputes the cursor from the
recorded slots. This rejects unplanned or excess evidence before changing
incident state while preserving out-of-order delivery and record restoration.
Fifteen focused investigation, persistence and stream tests passed on the
Stream A worktree; `git diff --check` passed before the commit.

This verifies only the offline policy component. A producer's identity,
source-local sanitization, freshness, connected read-only access, independent
diagnostic quality, and the M1 authority gate remain separate release
requirements. No live Aster service was changed.
