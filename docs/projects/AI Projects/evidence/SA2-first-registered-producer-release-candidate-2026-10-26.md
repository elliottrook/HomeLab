# SA2 first registered producer release candidate — 2026-10-26

## Scope

This candidate connects one pending SA1 decision to one fixed, in-process
SA2 observation: `aster-gateway/status`. The authenticated caller cannot choose
the producer or target. No network, filesystem, subprocess, credential, model,
repair or automatic-routing capability is introduced.

## Frozen packet

| Installed path | Candidate SHA-256 | Prior live state |
|---|---|---|
| `/opt/aster-agent/aster_agent.py` | `28f2e2f611ade77fac0f054fa0d238e4c575075d8013d5548d2810d1b9dfc703` | `3915413d0190456456aa419d583e8c8dc69805a7c3e21a849efab3cad8eefd0a` |
| `/opt/aster-agent/sysadmin_registered_producer.py` | `5c112b670e42e50ee63a7658253197937663ae0775c623e3e92345e23193f931` | absent |

The exact installer is
`services/aster-agent/deploy/install_sa2_registered_producer.sh`. It refuses
unexpected live bytes or a pre-existing new module, checkpoints the gateway,
imports the combined candidate, atomically installs two files and restarts only
`aster-agent.service`. Failure restores the gateway, removes the added module
and restarts Aster Agent. It never names or controls the llama service.

## Validation

- dependency-free incident/selector/producer regression: **35/35** with
  `ResourceWarning` fatal;
- LXC104 production-dependency producer and authenticated-route suite:
  **10/10**;
- installer syntax and contract: **4/4**;
- installed SA1 predecessor and absent producer rechecked before freezing;
- Aster Agent and accepted llama service remained active with unchanged PIDs
  and zero restarts throughout candidate testing.

## Remaining gate

Deployment requires one Aster Agent restart. Postchecks must verify the two
installed hashes and custody, service health, default authentication denial and
an unchanged llama PID/restart count. No live incident or observation is needed
to validate this release; a later user-triggered incident remains the only path
to consume the producer.
