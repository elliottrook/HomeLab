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

## Corrected dormant candidate

Platform commits `5a9c3471`, `a8551a18`, `95549522` and `b6a9f08e` implement
the reduced candidate and close the follow-up review findings. The candidate:

- installs only two absent Proxmox modules and four absent LXC110 runtime files
  plus one absent fixed wrapper;
- pins the actual live runner at SHA-256
  `6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2`,
  verifies `WORKLOAD_NOT_REGISTERED`, and requires the SA3 identity to remain
  absent from both runner and live manifest;
- leaves the working CLI, reservation ledger, runner, manifest, guardian and
  runtime unchanged;
- builds one deterministic archive at SHA-256
  `224647fe1815e30b8d74b3a1cceccf39ba3fa9712c3f561fdf9e5b0ceba5aaf7`;
- uploads only into a freshly absent root-only Proxmox incoming directory,
  requires a freshly absent stage and checkpoint, and verifies exact custody
  and digest before extraction;
- checkpoints all seven dormant target paths, installs atomically, runs target
  imports and rolls both Proxmox and LXC110 back on any write, postcheck or
  import failure; and
- retains uncertain checkpoint/failure evidence rather than retrying.

The complete platform source suite passes 62/62. A final read-only preflight
found the incoming, stage and checkpoint paths absent. The packet remains
source-only; no bundle was uploaded and no target file was installed. The next
gate is one explicit approval for the exact dormant staging transaction. It
will not register the workload, acquire a lease, book Lab Hours, invoke a model,
change a service/timer or restart production.

## First authorized installation result and corrected candidate

The exact reduced archive was subsequently staged under root custody and the
fixed installer was invoked once. It stopped during the first LXC110 file
write because `/usr/local/libexec/local-ai-lease/full-inference-pilot` did not
exist in that guest. The bounded result was `LXC110_INSTALL_FAILED` with
`FileNotFoundError` for that exact parent. No retry was attempted.

Independent postcheck found both Proxmox file targets, all four LXC110 runtime
targets and the LXC110 wrapper absent. LXC110 remained running. The root-owned
host and guest checkpoints, incoming archive and extracted stage were retained
as failure evidence. No registration, booking, lease, model request, service,
timer or restart occurred.

Platform commit `3c2896b1` corrects the demonstrated defect. Its revised
transaction treats the exact root-owned mode-0755 guest runtime directory as
managed state: it accepts an existing exact directory or creates it, records
whether this transaction created it, and removes it on rollback only after the
installed files have been removed and the directory is empty. It uses fresh
`root-v2` stage and checkpoint identities, packet SHA-256
`b32c1b2a2dcb5f0e8673cb204d997710c034c8c1ec4dba762109b67b4fdb7255`
and deterministic archive SHA-256
`72057cfff49abd2b2ecaa85e3d9e9ed7bf79905b93d678f8f11a5b858568885a`.
The corrected suite passes 64/64, including absent-directory success and
failure rollback, and two independent builds are byte-identical.

The corrected live installation is a new exact host change and has not been
run. It requires a fresh approval; the failed candidate must not be retried.
