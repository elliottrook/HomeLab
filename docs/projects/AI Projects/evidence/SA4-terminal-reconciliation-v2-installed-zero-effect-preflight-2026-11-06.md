# SA4 terminal reconciliation v2 installed zero-effect preflight — 2026-11-06

The installed v2 chain passed its final-path no-argument boundary check. Before
the check, hashes were recorded for every retained v6 input, its terminal
summary, both one-use ledger files and the healthy canary. Runtime controls and
the observer exchange were absent.

The installed v2 runner was invoked once with one unexpected argument. It
failed closed with exit one and `SA4 runner accepts no arguments` before
opening transaction inputs or creating any effect state. No signer, authority,
controller, ledger transition, target operation, service action or restart
occurred.

Afterward every recorded hash was byte-identical: the uncertain terminal
ledger remains `f7dde1e0…3c1c`, the v6 summary remains `a6e6fb53…e3c3`, all
six inputs remain exact and the canary remains healthy at `4529dee5…1065`.
The operation lock, emergency stop and exchange remain absent; no v2 process
remains; the lease is `ready`; Aster Agent, llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are healthy.

This validates only the inert installed boundary. It does not cure or rewrite
the v6 result and does not authorize a repair. The next SA4 work is a distinct
inert-canary registration and release path that can prove complete v2 lineage
without redrifting or reusing the repaired target.
