# D4 candidate-g runner activation result — 2026-11-03

**PASS; candidate-g is installed and runnable only through Lab Hours controls.**

The corrected exact bundle `68ba4a16…38d0` passed the live-ledger precheck and
installed once. The only reserved rows were standing exclusive-stack windows
without a runner workload; no workload booking was reserved, claimed or
running. Lease/drain state and all locks were absent.

The runtime `b4fc31b0…4da9`, reserved runner `63c7a116…aba` and release manifest
`c970bd70…9886` now match under root custody. The root-only rollback checkpoint
is retained. Installed imports, full manifest validation and exact runner-kind
admission passed. No candidate unit, process, lease, lock or state exists.

LXC104/110/116, Aster Agent, the accepted aster-llama service, Speech,
`pvescheduler`, `pvestatd` and the Lab Hours Doctor timer remained healthy.
The pre-existing inactive dispatcher, News and EPUB timer states were unchanged.
No booking, service stop, model request, restart, retry, route or promotion
occurred.

The next effect gate is now concrete: query the authoritative ledger over the
full candidate run plus recovery reserve, create one exact booking for
`sa3-evidence-envelope-quality-v1`, and permit the normal dispatcher/runner to
claim it. Runtime must still fail closed on booking, whole-host lease,
shared-lock, accepted-production, quiet-host and restoration checks.
