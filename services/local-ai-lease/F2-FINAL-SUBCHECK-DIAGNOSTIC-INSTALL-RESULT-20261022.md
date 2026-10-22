# F2 final-subcheck diagnostic installation result — 2026-10-22

Status: approved one-file diagnostic installation completed; no activation or
cycle retry occurred.

The coordinator was installed at:
`/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py`

| Item | Evidence |
|---|---|
| Installed SHA-256 | `98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425` |
| Custody | `root:root`, mode `0644` |
| Rollback | `/root/aster-f2-final-subcheck-rollback-1ca66cee/f2_scheduled_release_candidate.py` |
| Rollback custody | root-only directory `0700`, file `0600` |
| Target-Linux focused validation | 14/14 passed against the installed path |
| Temporary transfer files | removed |

Recurring F2 timers remain disabled/inactive, and the spent 2026-10-22 units
remain absent. Lease state is ready; no F2 state, lock, or receipt exists.
Production guests, services, and the control plane are healthy. No scan,
activation, retry, receipt, lease, or F3 action occurred.
