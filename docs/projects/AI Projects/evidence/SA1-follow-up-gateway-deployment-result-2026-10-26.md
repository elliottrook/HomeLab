# SA1 follow-up gateway deployment result — 2026-10-26

## Result

**PASS.** Jason approved the exact four-file SA1 candidate and the one required
`aster-agent.service` restart. The rollback-capable installer completed with
`SA1_FOLLOWUP_GATEWAY_OK`; no rollback was needed.

The installed files now match the frozen candidate:

| Installed path | SHA-256 | Custody |
|---|---|---|
| `/opt/aster-agent/aster_agent.py` | `3915413d0190456456aa419d583e8c8dc69805a7c3e21a849efab3cad8eefd0a` | `root:root 0644`, one link |
| `/opt/aster-agent/sysadmin_incident_store.py` | `c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb` | `root:root 0644`, one link |
| `/opt/aster-agent/sysadmin_incident_stream.py` | `90a927675178d0fa344c570217bb3215a55770ac779946fd8c4218c60b64d47c` | `root:root 0644`, one link |
| `/opt/aster-agent/sysadmin_followup_selector.py` | `f6ce43d5b72ec56ecf82d7257551bcac5bcd20233e368373bb2a77441d1ae14d` | `root:root 0644`, one link |

The three replaced predecessors are retained under
`/var/lib/aster/sa1-followup-pre-gateway-20261027`, owned `root:root` with mode
`0700`. Their hashes independently match the preregistered live baseline.

## Postchecks

- Aster Agent is active at PID `17011` with `NRestarts=0` after the intentional
  restart.
- Unauthenticated `/v1/models` remains denied with HTTP `401`.
- The accepted `aster-llama.service` remained active at its pre-change PID
  `48161` with `NRestarts=0`; it was not restarted.
- Candidate hashes, owner, mode and link count were re-read from the installed
  paths after the service became healthy.
- The source-side incident and selector tests pass with resource warnings
  fatal, the installer contract passes, and the release candidate already
  passed its 50-test target-Python packet before deployment.

## Boundary retained

This release adds authenticated, state-bound follow-up selection and durable
journaling only. It cannot execute an observation, call a model, repair a
system, discover a new target or enable automatic routing. Connected SA2
read-only producers remain a separate release gate.
