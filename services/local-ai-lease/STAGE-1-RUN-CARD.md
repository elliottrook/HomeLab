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

1. Capture the backup artifact inventory and run the bounded archive integrity
   checks through the fixed source adapter.
2. Stop and runtime-mask only the four lab-conflicting units.
3. Take two fixed Proxmox-owner quiescence samples at least ten seconds apart.
   Require inactive consumers, inactive News timer, unchanged start markers and
   healthy control plane.
4. Write the receipt only through the root-owned boundary envelope, bound to
   the current lease ID and generation. A hand-built evidence object is not
   accepted by the admission gate.
5. Review the receipt and lease state manually. Do not enable the watchdog or
   start a benchmark as part of Stage 1.

## Rollback

- If any check fails, retain the lease as degraded/unknown and do not admit lab
  work.
- Remove the temporary receipt, remove runtime masks, and restore the four
  recorded units to their prior states.
- Verify Aster Agent, llama.cpp, Aster Speech, News timer and the control plane
  are healthy before ending the window.
- Record the failure category and preserve the raw receipt inputs; do not relax
  host-key, source, timeout or custody checks.
