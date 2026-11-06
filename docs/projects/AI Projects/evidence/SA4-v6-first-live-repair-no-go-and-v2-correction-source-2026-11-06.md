# SA4 v6 first live repair NO-GO and v2 correction source — 2026-11-06

Jason approved the exact v6 one-use canary repair. Fresh owner and AI-PAM
proofs were created without exposing either private key. Immediately before
the effect, the whole-host lease was `ready`; the installed hashes, expected
drifted target digest and production health matched the release; and the input,
evidence, ledger, observer exchange, operation lock and emergency stop paths
were absent.

The fixed runner claimed grant `sa4-canary-first-grant-v6-20261106` exactly
once. It performed one atomic replacement, requested one independent observer
signature and took the `postcheck-complete` branch. The target changed from
`19b4e02d…df1a` to the exact healthy digest `4529dee5…1065`. The runner exited
zero, the LXC exchange and runtime controls were removed, the host bridge
request/response were retained in permanent root custody and their hashes
match the terminal exchange rows. The lease returned `ready`; LXC 104/110/116,
Aster Agent, llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd` remained
healthy. No retry, rollback, restart, route or promotion occurred.

This is nevertheless **NO-GO for SA4 milestone closure**. The first failed
gate is terminal reconciliation. The installed v1 reconciler was still the
older synthetic-only implementation: even after authenticated complete
postchecks it deliberately wrote `ledger_state=uncertain`,
`effect_outcome_accepted=false` and `manual_reconciliation_required=true`.
The grant is terminally burned with `use_count=1`. The fixed runner also
retained only its 688-byte terminal summary, not the full measurement,
checkpoint, source, claim, admission, effect terminal, postcheck, proof and
reconciliation artifacts. The retained summary digest is
`a6e6fb53…e3c3`; the terminal result names reconciliation digest
`012fc9ec…2d93`; the ledger record digest is `f7dde1e0…3c1c`. Those digests
cannot substitute for the missing canonical lineage, so the healthy physical
result is not retrospectively promoted to an accepted SA4 result.

The deterministic cause is now corrected in source-only v2 modules. A passing
authenticated postcheck burns the grant as `consumed`, records one effect and
zero retries, accepts the effect and clears manual reconciliation. A complete
rollback burns the grant as `failed`; uncertainty stays terminally uncertain.
The v2 controller streams every phase artifact through a fixed evidence writer,
and the v2 runner fsyncs and custody-validates the exact success or rollback
evidence set before removing the exchange or writing its terminal summary.
Historical v1 sources and release pins remain unchanged. The complete SA4
suite passes **229/229**.

The v2 sources remain inactive and grant no authority. Next is independent
source review, an exact reversible inactive-install packet for the four v2
modules, installed-path zero-effect validation and a fresh release against a
distinct inert drifted canary. The repaired v6 grant and target will not be
reused or deliberately redrifted.
