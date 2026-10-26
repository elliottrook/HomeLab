# F2 exact-cycle activation review — 2026-10-27

**Decision:** GO for one separately approved exact-cycle activation.

Stream A reviewed platform commit `9550e53a`, containing the fresh October 27
card, two nonpersistent timer candidates and three focused tests. Local focused
tests passed 3/3; the broader F2 suite completed 54 tests with 53 passes and one
expected skip.

## Exact candidate

| Item | SHA-256 |
|---|---|
| Activation card | `2f79385dabd0807e24467ed3cd95429f1b8058d08eec5a3342a46388b4ffb0e5` |
| 01:15 preparation timer | `7551c94a7b3d367059724aecb7b32863ad341fa9fb39a4ce08b04ea8d760493d` |
| 01:20 final timer | `2cdb512508ac4d889c4c1b94fdb6d42d95504cb721b2e450e7ad572b56592cd6` |
| Focused test | `20051c4b2b9227104445c2f4148bf147927f8026c5b562d98320723d16056b42` |

Target `systemd-analyze calendar` resolves the units to 01:15 and 01:20 PDT on
October 27. Read-only target validation matched all five installed source pins,
including corrected coordinator `6a1d520a…8193`; found the October 27 state
absent; and confirmed recurring timers disabled/inactive.

The card keeps F2 at its established early-cycle boundary after the 00:30
Proxmox backup and 01:00 TrueNAS task 1. Later backup/relay evidence remains an
F4/F5 dependency. It preserves October 19–26 evidence, allows no retry and
assigns observation-only cleanup to 01:42.

Activation remains a remote host change. It requires Jason's explicit approval
before installing/enabling only these two exact-date timers and creating the
one-occurrence reconciliation. No service is manually started, and no F3,
lease, consumer stop or model call is included.
