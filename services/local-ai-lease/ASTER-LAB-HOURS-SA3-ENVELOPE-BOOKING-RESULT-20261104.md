# SA3 candidate-g fresh booking result — 2026-11-04

Status: **GO — scheduled / conditional**

Jason approved the exact service-stop/start transaction. Immediately before
the reservation write, the authoritative ledger returned `state=clear` for the
complete window and the live baseline matched the reviewed card.

## Authoritative booking

- booking ID: `aster-stream-a-sa3-envelope-20261104-0930`
- owner: `aster-stream-a`
- workload: `sa3-evidence-envelope-quality-v1`
- start: `2026-11-04T09:30:00-07:00`
- end: `2026-11-04T11:00:00-07:00`
- state after write and independent reread: `scheduled`
- restoration buffer: 900 seconds

## Static and live preflight

The installed source producer, validator, registry, reserved runner and
candidate-g transaction matched the five reviewed hashes. The lease was
`ready`; shared drain state/lock and operation lock were absent; dispatcher,
Doctor, pvescheduler and pvestatd were active; LXC 104/110/116 were running;
Aster Agent, accepted llama/SYCL and Speech were active. EPUB remained in its
legitimate timer-inactive/worker-activating state admitted by the correction.

The dispatcher must still atomically claim the booking and recheck current
backup, lease, locks, installed pins, production health and competing work at
runtime. Any changed or uncertain gate is terminal NO-GO without service
effects or retry. The booking authorizes exactly one fixed transaction and no
model change, retry, extension, routing promotion, tool grant or recurring
schedule.
