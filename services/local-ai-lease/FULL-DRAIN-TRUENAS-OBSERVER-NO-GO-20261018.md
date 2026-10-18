# Full-drain TrueNAS observer route — NO-GO — 2026-10-18

The full-drain source producer requires a fixed read-only Proxmox-side SSH
observer for `midclt call rsynctask.query`.

Bounded read-only diagnostic from the current workstation on 2026-10-18:

- TCP/22 to `192.168.20.40` timed out after the five-second connect limit;
- the target-only identity path `/etc/local-ai-lab/truenas_schedule_observer`
  was absent locally, so no authentication was attempted here;
- delegated Proxmox-side nested observation also produced no output and timed
  out before termination.

Result: **NO-GO**. No TrueNAS schedule/task JSON was accepted, no staging or
host mutation occurred, and this route cannot support a mirror, F2, or F3
claim. The full producer still fails closed on this route. The separately
reviewed narrow isolation pilot may use local Proxmox current-cycle artifact
and completed-task proof without treating this observer as authoritative; that
pilot does not mutate backup/model files and does not claim F2/F3 completion.
Revalidation requires the target Proxmox host's pinned key/known-host custody,
bounded SSH reachability, and valid `rsynctask.query` JSON with the exact
task/order/date checks.
