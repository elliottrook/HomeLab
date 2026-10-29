# SA3 booked evaluation first-run result — 2026-10-29

Status: **NO-GO, production restored; exact correction installed**

Booking `aster-stream-a-sa3-20261029-1335` claimed exactly at 13:35 PDT.
The fixed transaction stopped the declared consumers under the durable drain
and guardian. The guest listener exited before readiness; no model result was
accepted or retained.

The owner restored every consumer. Terminal evidence records
`first_failure_phase=owner-transaction`,
`failure_code=OWNER_TRANSACTION_FAILED_RESTORED` and
`production_restored=true`. Postcheck found no drain state/lock, operation
lock, listener, lab scope or private credential directory. Production and
timers were healthy, the lease was ready and Doctor was healthy.

The exact cause was reproduced: the accepted model path is a root-owned
symlink to the content-addressed blob, while the old wrapper rejected every
symlink. The blob hash was correct but its `ollama` owner could write it.
Custody is now root:`ollama` mode 0644; model bytes, model selection and service
are unchanged.

Source correction `12266c7a` accepts only the exact link text and target,
root-owned single-link mode-0644 target and accepted hash. It retains a bounded
guest error code and stops a spent guardian after verified restoration. Its
64/64 suite passes. The exact host adapter, runner and manifest plus guest
wrapper were checkpointed and installed; imports, manifest and guest pins pass.

After the restoration buffer, the ledger was clear for 13:55–14:55 PDT. Fresh
booking `aster-stream-a-sa3-20261029-1355` is scheduled for that window. The
failed booking is not retried.
