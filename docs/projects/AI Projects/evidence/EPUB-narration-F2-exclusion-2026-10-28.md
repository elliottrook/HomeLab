# EPUB narration exclusion for the October 28 F2 cycle

## Result

The ongoing EPUB narration compiler was identified as a material competing
workload for the October 28 backup and F2 archive-integrity window. It runs in
LXC116, consumes up to three CPU cores, writes private narration state, and can
continue for hours. LXC116 is one of F2's three fixed archive identities.

The recurring worker timer was disabled at 10:33 PDT on October 27 without
stopping the active worker. This allows the current atomic book attempt to
finish normally but prevents another attempt from starting. Two root-owned
date-specific Proxmox timers are active:

- `epub-narration-quiesce-20261028.timer` stops any remaining worker and its
  timer at 00:15 PDT, leaving fifteen minutes before the 00:30 backup;
- `epub-narration-resume-20261028.timer` re-enables the recurring worker timer
  at 03:50 PDT, after the protected backup, F2 and conditional F3 sequence.

The worker's queue is durable. If the 00:15 stop interrupts the current attempt,
the next worker invocation records it as interrupted, removes its private
staging directory and requeues it while below the bounded attempt limit. No
book content, narration output or private path was inspected or retained in
this evidence.

Post-installation inspection confirmed both exclusion timers active/enabled,
both October 28 F2 timers still active/enabled, and the recurring EPUB worker
timer disabled. F2's existing load and competing-process gates remain
fail-closed: if quiescence does not complete or host load remains unsuitable,
the cycle must record NO-GO rather than begin the archive scan.

This is a one-cycle exclusion and restoration boundary. It does not change the
narration model, queue policy, source library, generated artifacts, F2 source,
backup schedule, lease state or production Aster services.
