# M3 K2 inactive install and development booking — 2026-11-06

## Inactive installation

The first platform preflight found that the installed Lab Hours release was
newer than the source branch and stopped before mutation. K2 was rebased onto
the exact 53-pin installed release, preserving the current MuseTalk, TTS,
EPUB, dispatcher and retry controls. A first installer attempt then failed
before writing because the measured root-owned platform files were mode 0644,
not the older template's expected modes. The corrected installer bound those
four exact hashes and modes and completed inactive:

- host files replaced: 4;
- host entry points added: 3;
- guest files added: 9;
- shared guest dependencies verified unchanged: 4;
- combined release manifest pins: 56;
- rollback checkpoint: retained;
- service restart: false;
- workload/model effect: not attempted;
- booking at install time: absent.

The final bundle SHA-256 was
`c29ab3426ee78b6b99afe88bb7f042e93891f9d7a627a28e2058002a2c96842b`.

## Reservation

The authoritative ledger rejected 16:20–17:20 and 19:00–20:00 because of
existing bookings. It returned clear for the complete 20:00–21:00
America/Vancouver window. The fixed registered workload was then reserved as:

- booking: `aster-stream-a-m3-k2-20261106-2000-r1`;
- workload: `m3-k2-shortlist-arbitration-development-v1`;
- owner: `aster-stream-a`;
- start: `2026-11-06T20:00:00-07:00`;
- end: `2026-11-06T21:00:00-07:00`;
- requests: 192;
- retries: 0;
- execution deadline: 1800 seconds;
- recovery reserve: 900 seconds;
- promotable: false.

The authoritative dispatcher timer is enabled and active. The scheduled run
still fails closed unless the fresh installed-pin, reservation, whole-host
lease, operation-lock, production-health and restoration gates pass. Sealed
evaluation, tools, routing and promotion remain off.

### Same-day readiness correction

A later use of the standard Lab Hours checker exposed a deterministic pre-start
defect: its generic validator looked for K2's private runtime pins on the host,
although the reviewed installer correctly holds them in LXC110. The platform
validator was corrected to inspect the actual guest custody and dependency
closure while preserving the newer B60 R5 registration. The inactive two-file
correction retained rollback and caused no restart or model effect.

After installation the standard checker returned `ready` with every check
true: booking/owner/window/recovery, dispatcher, exact registered release and
12 guest pins, lease, locks and bounded session contract. This removes the
specific admission fault that would otherwise have prevented tonight's
workload from starting.

## Observation readiness

A separate content-free reconciler now checks the authoritative booking,
root-custodied terminal, bounded owner receipt and retained-result digest as
one transaction. Its focused transaction, reconciliation and admission suite
passes 11/11; the platform's combined K2 and refreshed reserved-runner suite
passes 28/28. A one-time same-thread observation is scheduled for 21:05
America/Vancouver, after the booked recovery reserve. It cannot invoke, retry,
reschedule or promote K2.
