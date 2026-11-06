# SA4 fixed transaction runner source — 2026-11-06

The missing no-argument effect entry point is now source-complete at
`d48e26d5…b74e`. It reads only six fixed root-custodied inputs, authenticates
the exact plan/grant, initializes the compiled target's one-use ledger, creates
the fixed exchange directory and assigns bounded monotonic phase epochs.

It invokes only the installed root owner through the one-shot controller. The
observer callback can request exactly one success signature or two rollback
signatures. Signature-count drift, input custody drift or any exception stops
with runtime/ledger evidence retained. Terminal success hashes the exchange
evidence, removes the runtime exchange and writes one exclusive root-only
terminal result. It accepts no command-line arguments and has no retry path.

Four focused tests cover fixed success, input custody, argument rejection and
uncertain signature-count retention. The complete SA4 suite passes 198/198.
The runner is source-only. Next is its exact inactive-install review and result
verifier; no repair approval is currently active.
