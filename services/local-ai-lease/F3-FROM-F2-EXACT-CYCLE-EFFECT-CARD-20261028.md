# F3 retained receipt from F2 — October 28 exact-cycle effect card

Status: **SOURCE AND INACTIVE INSTALL PASS; CONDITIONALLY AUTHORIZED BY JASON'S DAYTIME-TO-TONIGHT TEST DIRECTION**

This card permits one bounded F3 conversion only after the October 28 F2
result is independently reconciled as complete. Jason authorized using the
day to stabilize the chain and testing it against tonight's fresh backup to
secure lab hours. It does not authorize F2, another archive scan, a retry, F4,
a lease, a service stop, a restart or a model call.

## Frozen implementation

| Installed path | SHA-256 |
|---|---|
| `/usr/local/libexec/local-ai-lease/f3_from_f2_result.py` | `64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421` |
| `/usr/local/libexec/local-ai-lease/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `efe8bc99efd95ce85d2dbe3c8218419fdb187ceaa065cf59a906e7c0323987ec` |
| `/usr/local/libexec/local-ai-lease/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |

## Exact admission

Run only after the 01:42 observation-only reconciliation accepts the October
28 F2 state as complete, with exactly three independently validated exit-zero
rows and every production postcheck passing. The result must remain within the
converter's three-hour bound.

Require the exact root-owned mode-`0600`, one-link canonical state at
`/var/lib/local-ai-lab/f2-scheduled/2026-10-28.json`; both spent exact-date
timers removed; recurring timers disabled/inactive; exact installed hashes and
custody; absent retained receipt; root-owned mode-`0700` receipt parent;
`local-ai-lease status` exactly ready with no lease or operation lock; no
F2/`zstd`/backup/pull/maintenance process; and healthy LXC104/110/116, Aster,
accepted llama.cpp/SYCL, Speech, Proxmox daemons and fixed schedules.

Any missing, failed, stale, changed or uncertain gate is terminal **NO-GO**.
Do not invoke the converter and do not retry in this cycle.

## One permitted effect and postcheck

Invoke exactly once as root:

`/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/f3_from_f2_result.py`

Accept only exit zero with content-free `complete`, `receipt_written=true`,
`archives=3` and a receipt SHA-256. Open the receipt without following links;
require root:root `0600`, one regular link and bounded canonical JSON. Verify
it independently against current fixed inventory/paths, reread unchanged F2
bytes, and retain only the receipt digest plus bounded archive identities and
timings. Recheck no converter/F2/`zstd` child, lease or lock and unchanged
production/schedules.

Preserve the receipt and F2 state on success, failure or uncertainty. Never
delete or overwrite an uncertain receipt. F3 success closes only F3. F4 must
use a subsequent fresh backup cycle and a separate effect decision.
