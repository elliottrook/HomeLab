# Full-drain TrueNAS observer route — NO-GO — 2026-10-18

The full-drain source producer requires a fixed read-only Proxmox-side SSH
observer for `midclt call rsynctask.query`.

Bounded read-only diagnostic from the current workstation on 2026-10-18:

- TCP/22 to `192.168.20.40` timed out after the five-second connect limit;
- the target-only identity path `/etc/local-ai-lab/truenas_schedule_observer`
  was absent locally, so no authentication was attempted here;
- delegated Proxmox-side nested observation also produced no output and timed
  out before termination.

Result: **NO-GO**. No TrueNAS schedule/task JSON was accepted, no current-cycle
backup proof was produced, and no staging or host mutation occurred. The source
producer fails closed on this route. Revalidation requires the target
Proxmox host's pinned key/known-host custody, bounded SSH reachability, and
valid `rsynctask.query` JSON with the exact task/order/date checks.
