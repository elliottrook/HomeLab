# SA3 expanded-source quality inactive-install preflight — 2026-10-29

## Result

**NO-GO for the initial inactive-install packet. No target was changed.**

The reviewed source transaction, listener adapter and guest wrapper were ready,
but a read-only Proxmox preflight disproved the packet's assumed platform
baseline before staging or installation. The candidate therefore failed closed
without a checkpoint, write, service action, model request or restart.

## Measured mismatch

The initial packet treated sixteen current platform modules as unchanged
prerequisites. The live pilot directory instead contains an older working Lab
Hours baseline:

- `lab_hours_inactive_target.py` and `lab_hours_workloads.py` are absent;
- `lab_hours_booking_cli.py` is SHA-256 `d035803e65e9384f671e625f266bab5a13e408eeb065e9007d82743f4c6eb793`, mode `0755`;
- `lab_hours_reservations.py` is SHA-256 `f3f112c31c30776e94889d1a372b0584b9460007369fc7986a3c5f90e6c92322`, mode `0755`;
- `lab_hours_reserved_runner.py` is SHA-256 `6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2`, mode `0755`;
- the installed release manifest is SHA-256 `b2c61494d572e17f3f1d4c71564f1b8c8f43728d9063c8d39e0c49e637593bed`; and
- the deadline guardian and runtime are mode `0755`, rather than the packet's assumed `0644`.

The existing fail-closed runner remains installed. The three proposed SA3 host
modules and all five proposed LXC110 targets are absent. The two proposed host
unit paths and two proposed guest unit paths are also absent. The guest runtime
contains neither the answer key nor independent-review material.

## Decision

Do not upgrade or replace the working Lab Hours core as part of an inactive
Aster quality candidate. Redesign the packet to add only the dormant SA3
transaction and listener adapter on Proxmox plus the four runtime files and
fixed wrapper in LXC110. Prove imports against the measured live baseline and
leave CLI, reservations, runner, manifest, guardian and runtime untouched.

Runner registration and any manifest/core update remain a later, distinct
reviewed effect gate. An exact fixed bundle, target import proof, reversible
installer and separate live installation approval are still required before
the dormant files may be staged.
