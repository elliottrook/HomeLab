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
