# SA1/SA2 current incident modules deployment result — 2026-10-26

## Result

**PASS; THE CURRENT INCIDENT CONTRACT IS LIVE.** The three reviewed incident
modules were installed in LXC104 and only `aster-agent.service` was restarted.
The live hashes are:

| File | SHA-256 |
|---|---|
| `sysadmin_incident_store.py` | `5a72b9f9c16ff66c64ac4d93d7f4f6ae9f3a7fe61d7a377efca237a95120e555` |
| `sysadmin_incident_stream.py` | `2154598ed14c7364a1ddc03b2c5f39ec1722b25b45de034e629965d46be78971` |
| `sysadmin_investigation.py` | `1f903f4a702d1548783990c38954d4e21a3688f83a062e42416183c7949481ed` |

The gateway remained at the accepted SA0 SHA-256
`e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116`.

## Rollback and postchecks

The three predecessors are preserved under
`/var/lib/aster/sa1-sa2-pre-incident-modules-20261027` with their exact reviewed
hashes. The directory is `root:root 0700`; each file is `root:root 0644`.

- `aster-agent.service` is `active/running`, PID `16653`, `NRestarts=0`.
- `/health` returned exactly `{"status":"ok","service":"aster-agent"}`.
- unauthenticated `/v1/models` returned HTTP `401`.
- `aster-llama.service` remained `active/running`, PID `48161`,
  `NRestarts=0`; it was not restarted or changed.
- the transient deployment packet and installer were removed.

The source candidate had already passed 33/33 target-environment tests with
`ResourceWarning` promoted to an error. This deployment closes the current
incident storage/presentation source drift and fixes the SQLite connection
leak. It does not itself complete SA1 or SA2: the live path still has only the
narrow fixed Doctor observation, and no adaptive follow-up producer, generic
diagnostic access, repair authority or automatic route was enabled.
