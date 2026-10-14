# Stage 1 source-receipt run card

Status: offline candidate. This run card does not authorize a live run.

## Preconditions

- Forgejo branch contains the pinned candidate and local focused tests are green.
- The overnight Proxmox backup and TrueNAS pulls have completed successfully:
  00:30 Proxmox, 01:00 guest pull, 02:00 LXC110 mirror, 03:00 Mac pull.
- The fixed TrueNAS host key and dedicated observer identity are present; no
  root SSH is used by the observer.
- The watchdog unit is absent or stopped and disabled; the candidate timer is
  not enabled. No benchmark or recovery effect may start automatically.
- Operator confirms the exclusive lab window and records the current active
  states of Aster Agent, llama.cpp, Aster Speech and the News timer.
- Control-plane services and UPS/network access remain healthy.

## Run sequence

1. Capture the backup artifact inventory, the content-free fixed-path Mac pull
   summary for `/mnt/Recovery/configuration/mac/`, and run the bounded archive
   integrity checks through the fixed source adapter. A TrueNAS task `SUCCESS`
   state alone is not sufficient; the Mac summary must have the expected root,
   same-night date, non-zero entry/byte counts, task-2 completion epoch,
   capture time within 900 seconds after that completion and before lease
   issuance, and a valid tree digest. The adapter acquires the summary only
   through the exact observer command `aster-mac-pull-summary`.
2. Stop and runtime-mask only the three Aster service units. Do not mask,
   disable, stop or modify the News timer under this run card.
3. Take two fixed Proxmox-owner quiescence samples at least ten seconds apart.
   Require inactive consumers, an already-inactive News timer, unchanged start
   markers and a healthy control plane. If News is active, stop and retain the
   lease as blocked; do not change its schedule.
4. Write only a candidate receipt through the root-owned envelope, bound to
   the current lease ID and generation. The envelope is not a trusted
   admission boundary and hand-built evidence is not sufficient for admission.
5. Review the receipt and lease state manually. Do not enable the watchdog or
   start a benchmark as part of Stage 1.

## Rollback

- If any check fails, retain the lease as degraded/unknown and do not admit lab
  work.
- Remove the temporary receipt, remove runtime masks, and restore the three
  recorded Aster units to their prior states. Do not alter the News timer.
- Verify Aster Agent, llama.cpp, Aster Speech, the unchanged News timer and the
  control plane are healthy before ending the window.
- Record the failure category and preserve the raw receipt inputs; do not relax
  host-key, source, timeout or custody checks.

## Bounded observer extension

The separately authorized live change, when approved, is limited to adding the
exact forced-command dispatch `aster-mac-pull-summary` to the existing
`aster-schedule-observer` identity. It may invoke only the root-owned wrapper
`/mnt/Media/.local-ai-lease/aster-mac-pull-observer-root`, which accepts no
arguments and runs the fixed observer. The observer reads task 2 and the fixed
tree, emits aggregate count/bytes/timestamps plus a SHA-256 digest, and emits
no filenames or file contents. It must not add root SSH, a general shell,
arbitrary path arguments or any additional sudo target.

Rollback is removal of that one dispatch, wrapper and sudoers target, followed
by a denied-command check and a repeat of the existing schedule/mirror probes.
