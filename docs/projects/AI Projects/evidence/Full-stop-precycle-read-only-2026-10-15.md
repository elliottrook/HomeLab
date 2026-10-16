# Full-stop pre-cycle state — October 15, 23:29 Vancouver

**Method:** direct, read-only `ssh -o BatchMode=yes proxmox` queries before
the October 16 backup cycle. No lease, scan, model call, host write, timer
change or service restart was attempted.

| Observation | Result | Limit |
|---|---|---|
| `local-ai-lease status` | `state: ready` | Point-in-time only; recheck before the archive scan and any later admission. |
| `systemctl is-enabled local-ai-lease-watchdog.timer` | `disabled` | Independent live recovery is not armed. |
| `systemctl is-active local-ai-lease-watchdog.timer` | `inactive` | Synthetic watchdog tests do not substitute for live recovery. |
| Installed `retained_archive_producer_candidate.py` SHA-256 | `f3ae1a83f16e5b9c1bca571826029603e4c8d88fc6b529bfe79ffcd465288a3b` | This is the earlier disabled-install pin, not the newer source-only CLI candidate `7f1c15a4`. |

This observation changes no F2–F9 checkbox. F2 still awaits exact current-cycle
backup and three completed archive tests. F3 still needs a separately approved,
installed trusted receipt producer. F6 cannot pass while the independent
watchdog is disabled. The conditional 01:10 check is read-only; no live drill
is scheduled or authorized from this record.
