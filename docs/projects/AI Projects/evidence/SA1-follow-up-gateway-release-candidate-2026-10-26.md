# SA1 follow-up gateway release candidate — 2026-10-26

## Scope

This candidate advances the deployed incident foundation by adding one
authenticated, effect-free follow-up journal boundary. It does not run an
observation, contact a target, call a model, change routing, grant authority or
restart the inference service.

The route is `POST /v1/sysadmin/incidents/{incident_id}/follow-up`. It requires
the existing signed-in owner boundary; the legacy API key is denied. The exact
request shape carries a strict schema version, the opaque current-state digest,
a bounded hypothesis, a disposition and, only for `observe`, one registered
unfilled target/kind pair. Stale, malformed, cross-incident, duplicate-pending
and unplanned proposals fail closed.

## Candidate

| Installed path | Candidate SHA-256 | Prior live state |
|---|---|---|
| `/opt/aster-agent/aster_agent.py` | `3915413d0190456456aa419d583e8c8dc69805a7c3e21a849efab3cad8eefd0a` | `e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116` |
| `/opt/aster-agent/sysadmin_incident_store.py` | `c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb` | `5a72b9f9c16ff66c64ac4d93d7f4f6ae9f3a7fe61d7a377efca237a95120e555` |
| `/opt/aster-agent/sysadmin_incident_stream.py` | `90a927675178d0fa344c570217bb3215a55770ac779946fd8c4218c60b64d47c` | `2154598ed14c7364a1ddc03b2c5f39ec1722b25b45de034e629965d46be78971` |
| `/opt/aster-agent/sysadmin_followup_selector.py` | `f6ce43d5b72ec56ecf82d7257551bcac5bcd20233e368373bb2a77441d1ae14d` | absent |

The exact installer is
`services/aster-agent/deploy/install_sa1_followup_gateway.sh`. It requires the
three prior live hashes and the selector's absence, checkpoints the three
replaced files under a new root-only directory, imports the combined candidate,
atomically installs the four files and restarts only `aster-agent.service`.
Failure restores the three originals, removes the new selector and restarts the
gateway. It neither names nor controls the llama service; the Proxmox-side run
must independently prove the accepted LXC110 unit retained its PID and restart
count.

## Verification

- dependency-free source suite: **45/45** with `ResourceWarning` fatal;
- installed Python 3.13/production-dependency packet in LXC104: **50/50** with
  `ResourceWarning` fatal;
- installer syntax and contract: **8/8**;
- candidate compiles with the local Python cache redirected to `/private/tmp`;
- live predecessors rechecked immediately before freezing: all three hashes
  match, the selector is absent and Aster Agent is active with zero restarts;
- accepted `aster-llama.service` is active in LXC110 with zero restarts.

The target suite caught and corrected two pre-release defects: the state digest
had included clock-derived observation age, and gateway tests had reloaded a
new incident using an older synthetic clock. The digest now excludes only that
derived age while remaining sensitive to evidence, hypothesis and plan state.

## Remaining gate

Deployment requires one Aster Agent restart. After installation, verify exact
hashes and custody, health, zero restart loop, unauthenticated model discovery
HTTP 401, and unchanged accepted llama PID/restart count. The route remains a
journal boundary after deployment; connected SA2 producers and automatic
observation execution are outside this release.
