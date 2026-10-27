# Network workload exclusion for the October 28 F2 cycle

## Result

The ongoing EPUB narration compiler was identified as a material competing
workload for the October 28 backup and F2 archive-integrity window. It runs in
LXC116, consumes up to three CPU cores, writes private narration state, and can
continue for hours. LXC116 is one of F2's three fixed archive identities. A
network-wide schedule and process audit also found two other recurring callers
of the production inference endpoint: News ingestion in LXC114 and Paperless
summaries in LXC115.

The recurring worker timer was disabled at 10:33 PDT on October 27 without
stopping the active worker. This allows the current atomic book attempt to
finish normally but prevents another attempt from starting. Two root-owned
date-specific Proxmox timers are active:

- `epub-narration-quiesce-20261028.timer` runtime-masks and stops the News
  ingestion and Paperless summary services, then stops any remaining EPUB
  worker and its timer at 00:15 PDT, leaving fifteen minutes before the 00:30
  backup;
- `epub-narration-resume-20261028.timer` removes the two runtime masks, clears
  their transient failed states and re-enables the recurring EPUB worker timer
  at 03:50 PDT, after the protected backup, F2 and conditional F3 sequence.

The News and Paperless timers remain enabled throughout. Runtime-masking their
service units prevents an already scheduled timer event from opening a B60
request during the protected interval without changing either recurring
schedule. Installed service hashes match the locally verified candidates:
`ce0081ac...a9df` for quiesce and `4a6ef58b...0ace` for resume. Both exact-date
timers are active and enabled.

The worker's queue is durable. If the 00:15 stop interrupts the current attempt,
the next worker invocation records it as interrupted, removes its private
staging directory and requeues it while below the bounded attempt limit. No
book content, narration output or private path was inspected or retained in
this evidence.

Post-installation inspection confirmed both exclusion timers active/enabled,
both October 28 F2 timers still active/enabled, the News and Paperless timers
active/enabled, and the recurring EPUB worker timer disabled. F2's existing
load and competing-process gates remain fail-closed: if quiescence does not
complete or host load remains unsuitable, the cycle must record NO-GO rather
than begin the archive scan.

## Network-wide collision audit

The October 27 audit covered every running Proxmox guest and VM, Proxmox host
tasks/timers, established connections to the production inference port, the
shared lease state, and TrueNAS middleware jobs plus rsync, cron and snapshot
schedules. There was no active Proxmox task, TrueNAS middleware job, lease or
client connection to the production inference port at the observation point.

The fixed 00:30 Proxmox backup and TrueNAS task 1 at 01:00 remain mandatory
dependencies. TrueNAS tasks 3 and 2 remain at 02:00 and 03:00. The TrueNAS
01:30 video archiver operates on the separate Media pool and starts after the
measured local-disk F2 scan duration; it does not use B60 or the Proxmox backup
disk. The Wednesday 03:00 Jellyfin integrity job starts after the F2/F3 chain.
Neither was changed. Any later full drill that crosses 03:00 must treat the
Jellyfin job as a fresh competing-work gate and quiesce it in that drill's own
reviewed transaction.

Routine Proxmox log rotation occurs before F2. The daily Proxmox update and
other TrueNAS protection jobs occur after the F2/F3 chain. Local reporting and
health timers do not call B60. The observer still rejects an active backup,
pull, archive scanner, full-stop process, lease or excessive host load, so an
unexpected or overlong task produces NO-GO rather than overlapping the scan.

This is a one-cycle exclusion and restoration boundary. It does not change a
model, queue policy, source library, generated artifact, F2 source, backup
schedule or lease state. It temporarily blocks only the three identified
inference workloads and restores their normal scheduling afterward.
