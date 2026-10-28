# F3 from F2 exact-cycle result — 2026-10-28

## Decision

**TIMED TEST: GO — COMPLETE.**

The separately authorized converter was invoked exactly once after the
October 28 F2 reconciliation passed. Every fresh precondition matched: spent
exact-date F2 timers were absent, recurring F2 timers were disabled/inactive,
the four installed source hashes and root custody matched the frozen card, the
retained receipt was absent, its parent was root-owned mode `0700`, the lease
was exactly `ready`, no lock or competing job existed, and production services
and schedules were healthy.

The converter returned exit zero with `state=complete`,
`receipt_written=true` and `archives=3`. It wrote
`/var/lib/local-ai-lab/archive-integrity.json` once with SHA-256
`1e05f475f09579dd7bb23a3938b2f21200ff7f62f7dd668ff9eb7ab695a4a3dd`.

## Independent receipt verification

The receipt was opened with `O_NOFOLLOW` and independently checked as a regular
root:root `0600`, one-link, 1,296-byte canonical JSON file. The installed
retained-integrity verifier rebound it to the current fixed inventory and
unchanged archive paths and returned the same digest:

`retained-archive-integrity-sha256:1e05f475f09579dd7bb23a3938b2f21200ff7f62f7dd668ff9eb7ab695a4a3dd`

It contains exactly the three accepted F2 rows:

| VMID | Archive identity | Size | Inventory ctime | Start | Finish | Elapsed | Exit |
|---|---|---:|---:|---:|---:|---:|---:|
| 104 | `backups:backup/vzdump-lxc-104-2026_10_28-00_34_36.tar.zst` | 1,998,364,079 | 1,793,172,876 | 1,793,175,605 | 1,793,175,626 | 20.811 s | 0 |
| 110 | `backups:backup/vzdump-lxc-110-2026_10_28-00_39_45.tar.zst` | 43,643,206,318 | 1,793,173,185 | 1,793,175,626 | 1,793,176,056 | 429.528 s | 0 |
| 116 | `backups:backup/vzdump-lxc-116-2026_10_28-00_49_16.tar.zst` | 4,804,684,297 | 1,793,173,756 | 1,793,176,057 | 1,793,176,090 | 33.146 s | 0 |

The F2 state was reread unchanged at SHA-256
`3956f00e5b13fae00b80c063ae6792bdc517575ca203bce9e6e4a588d260e8c0`.
There was no converter, F2 or Zstandard child afterward. The lease remained
ready with no lock. Aster Agent, accepted llama.cpp/SYCL, Speech, both actual
News timers, `pvescheduler` and `pvestatd` remained healthy and scheduled.

This completes F3 only. Under the governing same-cycle correction, any F4
must bind these unchanged October 28 rows after the fixed 03:00 pull and needs
its own effect decision. This result authorizes no F4, lease, service stop,
restart, model call, retry or promotion.
