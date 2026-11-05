# SA4 corrected inactive installation — 2026-11-05

## Result

Jason approved the corrected 18-file inactive installation from Stream A
commit `cc2dfc84`. A fresh no-follow preflight found the three SA4 parent paths
absent. LXC 104/110/116, Aster Agent, accepted llama/SYCL, Aster Speech,
`pvescheduler` and `pvestatd` were healthy before the change.

The staged bundle matched all 18 compiled SHA-256 identities. The installation
created exactly:

- `/usr/local/libexec/aster-sa4`, root:root mode 0755;
- 17 root:root mode-0644 Python source files beneath that directory;
- `/var/lib/aster/sa4`, root:root mode 0700;
- `/var/lib/aster/sa4/checkpoints`, root:root mode 0700; and
- the drifted inert canary at `/var/lib/aster/sa4/canary-adapter.json`,
  root:root mode 0644, one link, SHA-256
  `19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.

The corrected dependency `nlu_threshold_policy.py` has installed SHA-256
`984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d`.
Every other installed digest matches the corrected packet. The independent
metadata check found 18 files and three directories with no unexpected owner,
group, mode, type or link count.

All 17 installed Python modules imported from the installed directory with
bytecode disabled. The installed registry resolved only
`sa4-lxc104-canary-adapter-v1`; the rollback checker accepted the exact drifted
canary; checkpoint storage contained zero entries. All three custody slots
reported `empty` with no public-key digest. An initial read-only report command
used the non-existent presentation field `state` instead of the compiled field
`status`; all imports had already completed, and the corrected read-only query
returned the expected three empty slots. No installed state was changed by
either query.

LXC 104/110/116 and all prechecked production services remained healthy after
installation. No `aster-sa4` unit exists. No service was started, stopped,
reloaded or restarted.

## Boundary

This is an inert installation, not a repair release. It created no key,
credential, grant, booking, lease, operation lock, checkpoint, receipt, repair,
retry, model change, route or production consumer. The canary is deliberately
drifted and has no active reader.

## Next gate

Prepare the exact custody/admission packet for the three already accepted key
roles. Key creation and custody installation require a separate credential
approval. No measurement, checkpoint or repair can become eligible until all
three public identities are independently installed and the complete
authority/observer composition passes. The first repair effect remains a later
exact immediate-approval gate.
