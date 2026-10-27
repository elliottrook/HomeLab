# SA2 inference-health producer deployment result — 2026-10-26

## Result

**PASS.** Jason approved the exact two-replacement release and one Aster Agent
restart. The rollback-capable installer completed with
`SA2_INFERENCE_HEALTH_OK`; no rollback was needed.

| Installed path | SHA-256 | Custody |
|---|---|---|
| `/opt/aster-agent/aster_agent.py` | `43af11c953fb63fdbc37cd7465fe69fb7b6d0c3cd64cff206d484e0398284613` | `root:root 0644`, one link |
| `/opt/aster-agent/sysadmin_registered_producer.py` | `b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd` | `root:root 0644`, one link |

Both predecessors are retained at their preregistered hashes under
`/var/lib/aster/sa2-pre-inference-health-20261027`, with the directory owned
`root:root` and mode `0700`.

## Postchecks

- Aster Agent is active at PID `17250` with `NRestarts=0` after the approved
  restart.
- Unauthenticated `/v1/models` remains denied with HTTP `401`.
- The accepted `aster-llama.service` remained active at PID `48161` with
  `NRestarts=0`; it was not restarted.
- Installed and rollback hashes, owner, mode and one-link custody match the
  frozen card.

This adds only the fixed, bounded `inference-server/status` health observation.
It makes no model request, sends no credential, and grants no repair or generic
network authority. No incident was created during deployment.
