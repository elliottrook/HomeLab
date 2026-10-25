# D3 ordinary job handling — offline revalidation, 2026-10-25

> Result: **SOURCE BOUNDARY PASS — LIVE RELEASE STILL DEFERRED**

The reconciled Companion and delegation sources were rechecked without
launching, replacing or signing the installed Mac app and without starting a
worker or model request.

## Verified behavior

- The native snapshot shows an answer only for a recorded `completed` state.
- `unknown` suppresses any unconfirmed answer and gives a fixed do-not-resend
  instruction even when server message text conflicts.
- A running row is presented as the worker's last report, not proof that work
  remains active.
- A completed row whose temporary answer has expired directs the owner to the
  supervised original-answer recovery path and does not suggest resubmission.
- Stop remains a request until a terminal worker receipt confirms the result.
- Usage is labelled as reported token usage, not a charge or remaining quota.
- The hidden manual path retains its separate durable, allowlisted failure
  categories and no-automatic-retry wording.

## Measured checks

- Full native Companion suite: **60/60 passed**.
- Targeted dependency-free delegation, usage, session, store, worker and
  integration suite: **66 passed, 5 dependency-gated skips**.

A broad system-Python discovery was also attempted but is not acceptance
evidence: that interpreter lacks the project's pinned `httpx` and `pydantic`
dependencies, and two unrelated cross-process provisioning fixtures cannot
exercise their process boundary in that environment. No dependency was
installed and those errors are not represented as job-handling passes.

## Boundary

This verifies the current source behavior only. It does not enable delegation,
submit a request, prove a real quota/provider failure, install a Companion
build, resume the deferred manual-Codex release, or grant automatic routing or
tools. A later product release still needs its own reviewed build/install and
ordinary-use observation.

