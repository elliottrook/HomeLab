# SA3 first-run correction — fixed custody and failure cleanup

Status: **source-complete correction after restored NO-GO**

Booking `aster-stream-a-sa3-20261029-1335` claimed exactly once, drained the
declared consumers, and failed before listener readiness. The owner transaction
restored production and the booking ended `NO_GO` with
`OWNER_TRANSACTION_FAILED_RESTORED`. Independent postcheck found no drain
state, shared lock, listener, scope or credential directory; all production
services and timers were healthy and the lease was ready.

The exact cause is model-path custody, not model content: the accepted model
path is a root-owned symbolic link to the content-addressed Ollama blob. The
old wrapper rejected every symlink before resolving it. The blob hash remained
the accepted SHA-256. The blob has now been hardened from owner `ollama` to
owner `root`, group `ollama`, mode `0644`; it remains readable but is no longer
writable by the runtime account. Model bytes, model selection and service are
unchanged.

The corrected wrapper accepts only the exact root-owned link text, exact
content-addressed target, root-owned single-link mode-0644 target and accepted
hash. It also emits one bounded content-free error code on failure. The host
adapter retains that code in the owner traceback instead of collapsing all
guest failures to a generic nonzero exit. The reserved runner now stops its
spent guardian after a fully verified restoration, but preserves the guardian
whenever drain state or lock remains uncertain.

The combined wrapper, adapter, transaction, runtime, runner, reservation,
registry and installer suite passes 64/64. This correction does not create or
reuse a booking and cannot retry the failed reservation.
