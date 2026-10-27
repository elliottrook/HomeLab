# SA3 candidate-E release packet pending review — 2026-10-27

## Result

A machine-checkable, source-only deployment packet now pins the four runtime
files needed to add candidate E's authenticated proposal route to LXC104. The
packet deliberately records independent review as `pending`; its validator
rejects any attempt to relabel that state as passed.

The current live predecessor was checked read-only. `aster_agent.py` is exact
SHA-256 `43af11c9…4613`; the three proposal modules are absent. The candidate
would replace that one file and add exactly the boundary, fixed transport and
journal composition modules. No install script has been created and nothing
was staged on the target.

## Frozen boundary

- source commit: `5607040e92ab35ba568cbe6780526a7318c6c51a`;
- four-file manifest SHA-256: `96215266d253548a8dee89930463521375abc181f9131f77d4b48e18adaa688a`;
- target: LXC104, `aster-agent.service` only;
- one Aster Agent restart would be required for a later installation;
- model restart/change, automatic routing, observation authority and repair
  authority are all explicitly false.

## Validation

- release validator tests: **4/4 passed**;
- dependency-free sysadmin regression: **69/69 passed**;
- current manifest validation reports four files, review `pending`, automatic
  routing false and repair authority false.
- an eight-file temporary test bundle (SHA-256
  `fb161d6071b5110b3cfc185e16b39285f758b6999ae8fa1ee3233305e1b0e95a`)
  passed **31/31** proposal and FastAPI gateway tests under LXC104's installed
  Python 3.13 dependencies. This includes owner-versus-legacy authentication,
  content-minimized output and the no-effect journal boundary;
- the temporary Mac, Proxmox and LXC104 copies were removed. Aster Agent stayed
  active with zero restarts. The accepted LXC110 llama service stayed active at
  PID `48161` with zero restarts. No model request ran.

## Remaining gates

The packet cannot be installed in its current state. A separate reviewer must
accept the exact candidate-E review packet. The resulting accepted review must
then be incorporated into a new exact manifest and a rollback-capable installer
must be reviewed. Installation and the required Aster Agent restart need their
own immediate approval. Tonight's F2/F3/full-Aster schedules remain untouched.
