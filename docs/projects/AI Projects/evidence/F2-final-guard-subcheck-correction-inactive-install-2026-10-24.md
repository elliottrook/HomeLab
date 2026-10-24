# F2 final-guard subcheck correction — inactive installation

**Installed:** 2026-10-24 America/Vancouver. **Source:** platform commit
`770107dfe5a7f0473f99be98675752fa7fa86b14`. **Authorization:** Jason
explicitly approved the inactive two-file diagnostic installation.

## Result

The prior installed hashes were re-read and matched the reviewed card before
replacement. A fresh rollback checkpoint was created at
`/root/aster-f2-final-guard-rollback-770107df-20261024` with root-only `0700`
directory custody and the two prior files preserved.

| Installed path | Installed SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684` | `root:root 0644` |
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` | `root:root 0644` |

Target-Linux bytecode imports passed and the focused installed-path suite
passed **24/24**. Temporary transfer files were removed.

## No-effect postcheck

- LXC104, LXC110 and LXC116 remained running.
- Aster Agent, accepted `aster-llama.service` and Aster Speech remained active.
- `pvescheduler` and `pvestatd` remained active.
- F2 prepare/final timers were absent and inactive.
- No lease state, lease lock, F2 receipt or archive-integrity receipt existed.
- No scan, schedule, lease, receipt, service stop, model call or F3 action ran.

## Decision

The diagnostic installation passed. The timed test is still **NO-GO / not
scheduled** because a fresh date-specific exact-cycle card has not yet been
prepared, independently reviewed and approved. The platform owner was asked
to prepare that inactive card using these installed hashes.
