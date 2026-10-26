# F3 retained receipt from F2 — October 26 exact-cycle effect card

Status: **SOURCE AND INACTIVE INSTALL PASS; EFFECT NOT AUTHORIZED**

This card permits one bounded F3 conversion only after the October 26 F2
result is independently reconciled as complete. It does not authorize F2,
another archive scan, a retry, F4, a lease, a service stop or a model call.

## Frozen implementation

| Installed path | SHA-256 |
|---|---|
| `/usr/local/libexec/local-ai-lease/f3_from_f2_result.py` | `64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421` |
| `/usr/local/libexec/local-ai-lease/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` |
| `/usr/local/libexec/local-ai-lease/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |

The converter source is commit `de23781c`. Its inactive installation is
recorded in `F3-FROM-F2-INACTIVE-INSTALL-RESULT-20261025.md`; target Linux
passed 27/27 tests.

## Exact admission

Run only after the 01:42 observation-only reconciliation has completed and
only while the successful F2 result is within its three-hour conversion age.
Require all of the following immediately before the effect:

1. `/var/lib/local-ai-lab/f2-scheduled/2026-10-26.json` is a root-owned mode
   `0600`, one-link regular file under its root-owned mode-`0700` directory.
   Its canonical schema is exactly `aster-f2-scheduled.v1`, cycle
   `2026-10-26`, final/complete with no failure fields and exactly three
   exit-zero archive rows for VMIDs 104, 110 and 116.
2. Independent reconciliation has accepted those same three bounded rows and
   every production postcheck. A missing, partial, malformed, changed,
   uncertain or NO-GO result refuses F3.
3. Both October 26 exact-date F2 timers have completed and been removed by the
   approved cleanup; recurring F2 timers remain disabled/inactive. No F2,
   `zstd -t`, backup, pull or maintenance process competes.
4. The four installed files above match their exact hashes and root custody.
   `/var/lib/local-ai-lab/archive-integrity.json` is absent and its parent is a
   root-owned mode-`0700` directory.
5. `local-ai-lease status` is exactly `ready`; no lease, lease lock, operation
   lock or other lab receipt exists. LXC104/110/116 and their accepted Aster,
   llama.cpp/SYCL and Speech services remain healthy. Proxmox control daemons
   and fixed schedules remain healthy.

Any failed, stale or uncertain condition is terminal **NO-GO** for this card.
Do not invoke the converter and do not retry in the same cycle.

## One permitted effect

Invoke exactly once as root:

`/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/f3_from_f2_result.py`

Accept success only when it exits zero and reports content-free state
`complete`, `receipt_written=true`, `archives=3`, and a receipt SHA-256. The
converter rereads unchanged F2 bytes before its atomic no-overwrite write. It
does not rescan an archive.

## Independent postcheck

Open the new receipt without following links and require `root:root 0600`, one
regular link and bounded canonical JSON. Independently run the installed
retained-integrity verifier against the current fixed inventory and paths;
require the same three VMIDs, archive identities, timings and exit-zero rows,
and record only the receipt digest and bounded identities. Reread the F2 state
and require unchanged bytes.

Recheck no converter/F2/`zstd -t` child, lease or lock; unchanged production,
schedules and disabled recurring F2 timers. Preserve the receipt and F2 state
on success, failure or uncertainty. Never delete or overwrite an uncertain
receipt.

F3 success closes only F3. F4 must use a subsequent fresh backup cycle and a
separate approval; F5/F6, candidate H and all model calls remain blocked.
