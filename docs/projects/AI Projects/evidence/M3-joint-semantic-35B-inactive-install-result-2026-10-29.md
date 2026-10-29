# M3 joint-semantic 35B inactive install result — 2026-10-29

## Result

**PASS / LIVE PUBLIC GATE READY FOR ITS RETAINED EFFECT APPROVAL.** The
source-ready candidate at Stream A commit `8f3b60e4` now has a complete Lab
Hours driver at platform commit `4670bb34` and an independently reconciled
inactive installation recorded at platform commit `15aa9d23`.

The target registration is fixed to
`m3-joint-semantic-35b-public-v1`: 24 calls, zero retries, 90 seconds per call,
a 3,600-second controller deadline, a 4,500-second minimum booking and a
900-second recovery reserve. It has no arbitrary command field. Fourteen
runtime inputs are hash-pinned and the installed 32-file release manifest
matches exactly.

## Live safety state

No live candidate effect occurred. The install created no schedule, booking,
unit or timer; acquired no lease or lock; mounted no artifact; restarted no
guest; and called no model. Target Python imports pass on Proxmox and LXC110.
The unflagged guest entrypoint remains disabled.

Postchecks found the lease `ready`, shared state and locks absent, no candidate
mount or M3/35B process, Lab Hours Doctor successful, all three guests running,
and Aster Agent, accepted 9B/SYCL, Speech, dispatcher and Proxmox daemons
active. The rollback checkpoint is retained at
`/var/lib/local-ai-lab/checkpoints/m3-35b-inactive-4670bb34`.

## Next exact action

The next M3 action is one live public-gate transaction. Before effects it must
obtain an authoritative conflict-free Lab Hours booking for this exact
registered workload, then claim the whole-host lease and shared lock and arm
the mount-aware recovery guardian. It will restart LXC110, mount only the
staged hash-pinned 35B artifact read-only and backup-excluded, run 24 public
synthetic requests, restore exact accepted production, and retain a
content-bounded result. It cannot open private calibration or holdout data,
promote a model, enable routing or retry an uncertain result.

This is the first remaining step that falls under Jason's retained requirement
for an exact model/restart approval. Routine Stream A preparation is complete.

