# SA2 inference-health producer release candidate — 2026-10-26

## Scope

This candidate extends the deployed fixed SA2 registry with exactly one
additional pair: `inference-server/status`. It contacts only the accepted
llama service's fixed `/health` endpoint, sends no credential or prompt and
accepts only its exact bounded health response.

## Frozen packet

| Installed path | Candidate SHA-256 | Prior live SHA-256 |
|---|---|---|
| `/opt/aster-agent/aster_agent.py` | `43af11c953fb63fdbc37cd7465fe69fb7b6d0c3cd64cff206d484e0398284613` | `28f2e2f611ade77fac0f054fa0d238e4c575075d8013d5548d2810d1b9dfc703` |
| `/opt/aster-agent/sysadmin_registered_producer.py` | `b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd` | `5c112b670e42e50ee63a7658253197937663ae0775c623e3e92345e23193f931` |

The exact installer is
`services/aster-agent/deploy/install_sa2_inference_health_producer.sh`. It
requires both deployed predecessor hashes, checkpoints both files in a new
root-only directory, imports and atomically installs the candidate, and
restarts only `aster-agent.service`. Failure restores both predecessors and
restarts Aster Agent. It never names or controls the llama service.

## Validation

- dependency-free incident/selector/producer suite: **37/37** with
  `ResourceWarning` fatal;
- LXC104 production-dependency producer and route suite: **12/12**;
- bounded live health observation: exact `inference-server/status`, state
  `ok`, fixed service/endpoint facts only;
- installer syntax and contract: **4/4**;
- both live predecessors and service PIDs were rechecked before freezing.

## Remaining gate

Deployment requires one Aster Agent restart. It must preserve both predecessors
for rollback, verify exact installed custody and authentication denial, and
prove the accepted llama PID/restart count remains unchanged. No model request
or live incident is required.
