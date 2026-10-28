# F2 exact-cycle result — 2026-10-28

## Decision

**TIMED TEST: GO — COMPLETE.**

The approved October 28 exact-cycle prepare and final timers both completed
successfully. The root-custodied terminal state is a regular root:root `0600`,
one-link file with SHA-256
`3956f00e5b13fae00b80c063ae6792bdc517575ca203bce9e6e4a588d260e8c0`.
Its outer and inner states are `complete`, the phase is `final`, and no
admission receipt was written.

## Independently validated bounded rows

The current fixed Proxmox inventory independently matched every recorded
VMID, volid, size and inventory ctime:

| VMID | Archive identity | Size | Inventory ctime | Start | Finish | Elapsed | Exit |
|---|---|---:|---:|---:|---:|---:|---:|
| 104 | `backups:backup/vzdump-lxc-104-2026_10_28-00_34_36.tar.zst` | 1,998,364,079 | 1,793,172,876 | 1,793,175,605 | 1,793,175,626 | 20.811 s | 0 |
| 110 | `backups:backup/vzdump-lxc-110-2026_10_28-00_39_45.tar.zst` | 43,643,206,318 | 1,793,173,185 | 1,793,175,626 | 1,793,176,056 | 429.528 s | 0 |
| 116 | `backups:backup/vzdump-lxc-116-2026_10_28-00_49_16.tar.zst` | 4,804,684,297 | 1,793,173,756 | 1,793,176,057 | 1,793,176,090 | 33.146 s | 0 |

The result contains exactly these three rows. The retained F3 receipt remains
absent. There was no F2 or Zstandard child, lease or lock after completion.

## Production postcheck and cleanup

LXC104, LXC110 and LXC116 were running. Aster Agent, accepted
`aster-llama.service`, Aster Speech, `pvescheduler` and `pvestatd` were active.
The actual News timer names, `news-aggregator-ingest.timer` and
`news-aggregator-digest.timer`, were active, waiting and enabled. The initially
queried shorthand `news-digest.timer` does not exist and was not treated as a
production failure.

Both spent October 28 F2 timers were stopped, disabled and removed under the
approved rollback, followed by `daemon-reload`. The recurring prepare/final
timers remain disabled and inactive. The shared lease returned exactly
`ready`; no trusted receipt was created by this reconciliation.

This completes F2 only. The separately approved 01:50 F3 conversion remains
conditional on its own fresh gates and may not infer authority for F4, a
lease, service stop, model call, retry or promotion.
