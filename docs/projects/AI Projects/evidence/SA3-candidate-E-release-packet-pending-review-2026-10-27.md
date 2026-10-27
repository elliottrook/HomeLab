# SA3 candidate-E reviewed release packet — 2026-10-27

## Result

A machine-checkable, source-only deployment packet now pins the four runtime
files needed to add candidate E's authenticated proposal route to LXC104. The
packet binds the independently reviewed PASS receipt at SHA-256
`09b19ca26…a9c6`; its validator rejects review or receipt drift.

The current live predecessor was checked read-only. `aster_agent.py` is exact
SHA-256 `43af11c9…4613`; the three proposal modules are absent. The candidate
would replace that one file and add exactly the boundary, fixed transport and
journal composition modules. No install script has been created and nothing
was staged on the target.

## Frozen boundary

- source commit: `5607040e92ab35ba568cbe6780526a7318c6c51a`;
- reviewed four-file manifest SHA-256:
  `15bc75939c9659de104516930c1ac201d0ff423f8232953acb1f68655583fa82`;
- candidate review: **PASS**, eight cases and four files independently
  verified;
- target: LXC104, `aster-agent.service` only;
- one Aster Agent restart would be required for a later installation;
- model restart/change, automatic routing, observation authority and repair
  authority are all explicitly false.

## Validation

- release validator tests: **4/4 passed**;
- dependency-free sysadmin regression: **69/69 passed**;
- current manifest validation reports four files, review `passed`, automatic
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

The packet still cannot be installed directly: a rollback-capable installer
must be written, tested and reviewed against the final manifest. Installation
and the required Aster Agent restart need their own immediate approval.
Tonight's F2/F3/full-Aster schedules remain untouched.
