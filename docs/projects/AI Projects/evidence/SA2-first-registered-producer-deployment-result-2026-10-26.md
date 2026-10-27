# SA2 first registered producer deployment result — 2026-10-26

## Result

**PASS.** Jason approved the exact two-file release and its one required Aster
Agent restart. The rollback-capable installer completed with
`SA2_REGISTERED_PRODUCER_OK`; no rollback was needed.

| Installed path | SHA-256 | Custody |
|---|---|---|
| `/opt/aster-agent/aster_agent.py` | `28f2e2f611ade77fac0f054fa0d238e4c575075d8013d5548d2810d1b9dfc703` | `root:root 0644`, one link |
| `/opt/aster-agent/sysadmin_registered_producer.py` | `5c112b670e42e50ee63a7658253197937663ae0775c623e3e92345e23193f931` | `root:root 0644`, one link |

The prior gateway is retained at
`/var/lib/aster/sa2-pre-registered-producer-20261027/aster_agent.py`. Its hash
is the preregistered `3915413d…efd0a`; the checkpoint directory is
`root:root 0700`.

## Postchecks

- Aster Agent is active at PID `17132` with `NRestarts=0` after the approved
  restart.
- Unauthenticated `/v1/models` remains denied with HTTP `401`.
- The accepted `aster-llama.service` remained active at PID `48161` with
  `NRestarts=0`; it was not restarted.
- Both installed files match their frozen hashes, owner, mode and one-link
  custody.

This enables only an owner-triggered in-process `aster-gateway/status`
observation that was already selected and journalled by SA1. It adds no generic
producer dispatch, model use, repair authority or automatic routing. No live
incident was created as part of deployment.
