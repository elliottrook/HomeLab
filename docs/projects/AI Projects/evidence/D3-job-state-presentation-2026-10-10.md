# D3 recorded-job status presentation — offline candidate

**Status:** local source candidate; no app or gateway deployment, worker start,
model request, or B60/llama use.

The disabled remote-worker job view previously used the same generic
“Waiting for Codex” text for queued, offered, accepted and running records.
That hides an important distinction: only a queued job can safely expire as
never offered; once offered, execution may be uncertain. The candidate now
describes those recorded stages separately and marks unknown or unrecognized
states as **do not resend**. The native list uses plain status labels. A stop
request still overrides the stage text until the worker confirms an outcome.

This changes presentation only. It does not change the ledger, dispatch,
authority, cancellation, retry, quota reporting or recovery rules. In
particular, offered is not described as “not started,” and running is framed
as the worker's last report rather than proof that work remains active.

Validation: four focused Companion tests passed after a local Swift build;
eighteen dependency-free handoff ledger tests passed; the Python route source
parsed successfully. The full route fixture could not run in the system Python
because FastAPI/Pydantic are not installed there. No dependency was installed.
Before any D3 release, run the route fixtures in the pinned application
environment and verify the screen through normal authenticated use. This
candidate does not satisfy the D3 release or job-handling milestone by itself.
