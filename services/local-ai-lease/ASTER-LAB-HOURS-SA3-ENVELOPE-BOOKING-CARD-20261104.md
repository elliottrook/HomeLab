# SA3 candidate-g fresh booking card — 2026-11-04

Status: **static GO; reservation and service effects not yet authorized**

## Exact proposal

- booking ID: `aster-stream-a-sa3-envelope-20261104-0930`
- owner: `aster-stream-a`
- registered workload: `sa3-evidence-envelope-quality-v1`
- start: `2026-11-04T09:30:00-07:00`
- hard end: `2026-11-04T11:00:00-07:00`
- attempts: one
- retries/extensions: zero

At 07:46 host-local time, the authoritative ledger returned `state=clear` for
the full proposed window. The reservation command must repeat `check-window`
immediately before the write and fail closed if the result changes.

## Corrected installed boundary

- source producer: `6103da31…13ad`
- final validator: `094d588b…f31`
- workload registry: `3bcfefd8…be73`
- reserved runner: `63c7a116…5aba`
- candidate-g transaction: `b906f30d…fa26`
- all five files: `root:root`, installed modes 0644/0755 as declared
- lease: ready
- shared drain state/lock and operation lock: absent
- dispatcher and Doctor timers: active
- LXC 104/110/116: running
- Aster Agent, accepted llama/SYCL and Speech: active
- EPUB timer: inactive; worker: activating, now admitted by the corrected rule
- pvescheduler and pvestatd: active

The spent November 3 booking remains terminal and is not reused.

## Effects and exclusions

If reserved and claimed, the fixed runner may stop the declared production
consumers, perform exactly the 14-request candidate-g prose workload, and
restore the accepted production services. This service stop/start is the only
remaining explicit owner decision.

The card does not authorize a model/backend change, package deployment,
arbitrary command, second attempt, deadline extension, routing promotion, tool
authority, J1 work, sealed-holdout access, Git push or recurring schedule.
Failure or uncertainty is terminal and must retain evidence and restore
production without retry.
