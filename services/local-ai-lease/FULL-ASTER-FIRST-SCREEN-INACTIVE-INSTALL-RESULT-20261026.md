# Full-Aster first-screen transaction — inactive install result

Status: **PASS / INSTALLED INACTIVE / NO LIVE EFFECT**

Jason approved the exact `cec8050f` card on October 26. The installer used the
source archive from `b6dc186eef865924294b4e5cb1ef72d73c149733`, checkpointed
the two exact F4/F5 predecessors in a new root-only directory, installed nine
new files and replaced only those two predecessors.

Independent post-install verification matched all eleven manifest SHA-256
values, root ownership, one-link custody and modes. The Proxmox modules are
0644, the host wrapper and LXC110 request helper are 0755. Target Linux passed:

- 22/22 full-Aster first-screen tests;
- 11/11 F4/F5 transaction and root-writer tests; and
- 62/62 existing full-inference regression tests.

The host wrapper refused a call without `--effect-authorized` before Python
started; the guest helper returned its exact disabled response without
`--run-authorized`. No request was sent.

Postchecks found the whole-host lease exactly ready; full-drain, guardian,
screen, admission, F4 and F5 runtime state absent; Stream A watchdog and owner
heartbeat timers disabled/inactive; LXC104/110/116 running; Aster Agent,
accepted llama.cpp/SYCL and Speech active; and `pvescheduler`/`pvestatd`
active. No service or guest restarted, no schedule changed, no mount was added,
no model bytes or custody changed and no model call occurred.

This closes only inactive installation. A live first-screen run still requires
fresh same-cycle F2-F5 evidence and a separate exact approval because it stops
and starts LXC110 while the independent guardian enforces a 30-minute effect
window plus 15-minute restoration reserve.
