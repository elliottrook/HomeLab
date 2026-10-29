# Aster Lab Hours reservation runbook

Lab Hours is an exclusive, booked transaction. The permanent dispatcher only
checks for due reservations; it does not create them and it never stops a
service when the ledger is empty.

## Booking contract

The authoritative ledger is `/var/lib/local-ai-lab/reservations` on Proxmox.
It is root-owned mode `0700`; records and the advisory lock are mode `0600`.
Bookings use canonical IDs, a registered workload, an offset-qualified start
and end, a maximum 90-minute outage, and a 15-minute restoration buffer.

Book with:

```text
/usr/local/sbin/aster-lab-hours reserve \
  --booking-id <unique-lowercase-id> \
  --owner <registered-owner> \
  --workload accepted-9b-direct-control-smoke-v1 \
  --start 2026-10-29T13:00:00-07:00 \
  --end 2026-10-29T13:30:00-07:00
```

Every supported AI scheduler must run `check-window` before proposing or
creating exclusive work. A non-empty result is reserved, including the
15-minute restoration buffer. An external scheduler's check is advisory; the
host runner is authoritative and independently requires an atomic, once-only
claim before any effect.

The initial registered workload is the accepted three-request 9B control
smoke. A second fixed registration exists only for the LH5 owner-loss recovery
exercise; it cannot run a user workload. Adding a model-test workload requires a separate root-owned,
hash-pinned registration. Arbitrary commands are never taken from booking
records.

## Runtime enforcement

`aster-lab-hours-dispatch.timer` checks once per minute. A due record starts a
fixed transient runner. The runner atomically changes `scheduled` to `claimed`,
verifies installed pins, the current backup, host exclusion, lease, production
baseline and absence of competing work, then arms the independent guardian.
The transaction stops the declared consumers, runs the registered workload,
and restores the accepted production configuration. Success or failure is
terminal in both the booking and its retained attempt evidence.

Concurrent supported work cannot bypass the record claim, shared operation
lock or whole-host lease. Root can always bypass a local policy; Doctor treats
an unreserved listener, lab process or drain state as unhealthy so such a
bypass is visible rather than silently accepted.

## Monitoring and recovery

`aster-lab-hours-doctor.timer` checks every five minutes. It reports missed
reservations, stale claims, malformed custody, unowned drain state,
unreserved lab processes/listeners, production service failures and lease
drift. It also reports the latest successful booked transaction.

If an owner is lost, the prearmed guardian fences only the exact owner scope,
uses the durable lease identity to run recovery, and restores production. Do
not delete state or locks to make Doctor green. If rescue is uncertain, retain
all evidence and reconcile the exact owner/guardian before another booking.

Cancel only a still-scheduled booking. Never overwrite or reuse a booking ID.
Rollback disables the dispatcher and Doctor timers, waits for or recovers any
claimed transaction, restores the checkpointed files, and leaves all booking
and attempt evidence intact.
