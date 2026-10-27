# SA3 candidate-E gateway install card — 2026-10-27

Status: **prepared and independently source-reviewed; not authorized or executed**

## Exact candidate

- reviewed release manifest SHA-256:
  `15bc75939c9659de104516930c1ac201d0ff423f8232953acb1f68655583fa82`;
- installer SHA-256:
  `981f13e065442ccfe0a07085b1fe31d091a094851163bf2377eb94aaa0cf4969`;
- installer test SHA-256:
  `0ebcac2d1183a3f2cefcf4fcdc8d91dfff726d4b5bdf2136412f8dfd37e09365`;
- candidate source commit: `5607040e92ab35ba568cbe6780526a7318c6c51a`;
- independent candidate review: **PASS** at exact review packet commit
  `7d3d35083334132dc4d3d6a00dfe097a264ea2a8`.

## Intended change

On LXC104 only, checkpoint the exact live `aster_agent.py` predecessor, replace
it with the pinned candidate, and add the three currently absent proposal
modules. Import the candidate and require the exact proposal route before any
install. Install all four files atomically, restart only `aster-agent.service`,
then verify health, zero service restart failures, authentication denial at the
existing API boundary and the new proposal route, exact hashes and root-owned
mode `0644` custody. The installer accepts no arguments and removes only its
fixed packet path. It requires all four `.new` paths absent before staging and
cleans them only after this run begins staging.

The change exposes an owner-authenticated request for one no-tool local proposal
and journals only its no-authority/no-effect decision. It does not automatically
call the route, execute the selected observation, repair a system, enable
automatic routing or add a schedule.

## Preconditions

1. The installed `aster_agent.py` is exact SHA-256 `43af11c9…4613`; all three
   proposal modules remain absent.
2. Aster Agent is active with `NRestarts=0` and no existing checkpoint occupies
   `/var/lib/aster/sa3-pre-proposal-gateway-20261027`.
3. The four staged source hashes match the reviewed manifest.
4. The protected F2/F3/full-Aster window is inactive; no overlapping operation
   depends on an uninterrupted Aster Agent.
5. Jason gives immediate approval for this exact installation and one Aster
   Agent restart.

## Rollback

Any failure after the first installed file restores the checkpointed
`aster_agent.py`, removes only the three newly added proposal modules, restarts
only Aster Agent, waits for the fixed health response, removes the staging
packet and reports rollback. The root-only predecessor remains after success.

## Validation already complete

- dependency-free sysadmin suite: **69/69**;
- LXC104 Python 3.13/FastAPI temporary packet: **31/31**;
- manifest and installer suite: **9/9**;
- shell syntax: pass;
- independent installer source re-review: **PASS**, with the fixed packet path,
  staged-file cleanup boundary, rollback, new-route authentication check and
  service scope verified against the exact hashes above;
- temporary target packet removed; Aster Agent and accepted llama service left
  unchanged; no model request performed.

## Explicit exclusions

No llama/model restart or change, B60 lease, model request, automatic routing,
producer execution, repair authority, incident creation, credential read,
Companion change, F2/F3/full-Aster change, schedule change or Git push is
included.
