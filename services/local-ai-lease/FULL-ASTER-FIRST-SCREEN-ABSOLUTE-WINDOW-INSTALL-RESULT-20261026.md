# Full-Aster first-screen absolute-window installation result — October 26

Status: **PASS / INSTALLED / TIMER REMAINS CONDITIONAL**

Jason approved platform candidate `75a2e279`. The exact installer required
live predecessor SHA-256 `328b41538451a47cf8ae3355c4a3f978c2cdc47cff848b856c1671178f0bca47`,
clear screen/guardian/full-drain state and the October 27 timer active. It
preserved the predecessor beneath the new root-owned mode-0700 checkpoint
`/var/lib/local-ai-lab/full-aster-first-screen-pre-absolute-window-20261027`
and atomically installed only
`full_aster_first_screen_launch.py`.

Independent post-install verification found:

- installed launcher SHA-256
  `11568103c134b98821aad4154e79645375f15f3021fdaf9ce232340d8ef24d66`,
  root:root mode 0644, one link;
- predecessor checkpoint exact, root:root mode 0644 within its root-only
  directory;
- installed target-Python contract accepts the exact 03:10 start and rejects
  03:31 before any effect;
- `full-aster-first-screen-20261027.timer` remains active for 03:10 PDT;
- lease state `ready`, with no screen, guardian or full-drain state;
- Aster Agent, accepted llama.cpp/SYCL and Speech active; Aster Agent and llama
  restart counts remain zero; and
- no launcher/controller/guardian process, model call, lease, mount, service
  restart, schedule edit or timer edit occurred.

The one-time transaction is now **GO — SCHEDULED / CONDITIONAL**. Fresh F2/F3,
03:00 pull, artifact/hash, quiet-host and production gates remain mandatory;
any failure is terminal NO-GO without retry.
