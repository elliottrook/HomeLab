# AsterTV v3 M7 — Bedroom content-only bridge candidate

Date: 2026-11-06 (America/Vancouver)  
Target: `AsterTV-Bedroom` / `192.168.1.140`  
Outcome: repository candidate complete; no live deployment authorized or made

This initial two-transform boundary record is retained for provenance. The
complete client-inclusive candidate and rollback runner supersede it in
`AsterTV-v3-M7-Bedroom-disabled-first-deployment-preparation-2026-11-06.md`.

## Read-only preflight

- The resolved target is `AsterTV-Bedroom`, not Family or Jen.
- Bedroom answered on its accepted address, Kodi was active with zero restarts,
  playback was idle and no player was active.
- Wi-Fi remained associated with `GoWest` at approximately `-54 dBm` and high
  negotiated bitrate. This candidate does not change the Wi-Fi or stereo
  contracts.
- The accepted Remote service remained
  `c28bf36e9b99159b1ee5bf22ae4d83d90b0c53a557de2c236e6d1b05cfba5d49`.
  Bedroom does not yet have the content-session publisher installed.
- Home Assistant's adopted Bedroom LG entity was unavailable at the time of
  inspection. That prevents accepting power, volume or mute authority.
- The live Aster gateway exposed the three accepted Remote client identities
  and only the existing `HA-Family` equipment identity. No Bedroom bridge key,
  identity or equipment authority existed.

No credential value, media title, account content or viewing history was read
or recorded.

## Ownership decision

The Aster gateway and Home Assistant component are shared external services.
Adding Bedroom support directly to their common source made the fleet compiler
correctly treat Family's frozen materializer as changed, even when the derived
Family bytes were normalized back to their accepted hashes. That would create
false desired-state drift on an already accepted production composition.

The candidate is therefore isolated at
`services/kodi/astertv-v3/bedroom_content_bridge/`. It derives two exact files
from hash-pinned accepted sources without changing Family, Bedroom or Jen's
current appliance compositions:

| Authority | Candidate destination | SHA-256 |
|---|---|---|
| Aster Agent | `/opt/aster-agent/aster_remote.py` | `66f85ee3e439276c25a5768ffe77cf2f252cdb394faaadab411f4100f632cd4c` |
| Home Assistant | `/config/custom_components/aster_room_bridge/contract.py` | `2c927737a82312c4fa9707d980a9c2bb3b92ff974d8cbce929c52249d87be82a` |

The sole capability change is acceptance of an authenticated room identity
whose equipment-action allowlist is empty. The gateway still denies every
equipment command, while the Home Assistant bridge can poll only the volatile,
content-free playback/class envelope. The manifest declares
`deployment_authorized: false`, excludes credentials and configuration, and
does not claim any appliance composition.

Family remains exactly frozen at composition
`a09ef2b5974a464738069caeb9fccab44c1feefc9d20763b83eb84bd92a79411`
and derived gateway `715b172a62e978ccaf79dfd3f9801da641cd067da72ad7187658efa9ccc0d73a`.

## Verification

- Bedroom candidate materialization: 2/2 passed and byte-deterministic.
- Home Assistant bridge suite: 20/20 passed.
- Remote client suite: 38/38 passed.
- Fleet composition/release suite: 54/54 passed.
- Fleet compile: three deployed compositions plus one Guest candidate; Family,
  Bedroom and Jen composition hashes unchanged.
- Exact gateway candidate `66f85ee3…cd4c` was previously replayed in Aster's
  pinned runtime: 13/13 tests passed from deterministic bundle
  `061e9178e63218f7f7b94ab2313db3f7f4afdf3669c19a932475b13eb1a87f90`.
  The live Aster process/hash did not change and no temporary payload remained.

## Separate live-effect gate

Deployment remains a later bounded operation. It requires:

1. fresh identity, idle-playback and Bedroom-display release checks;
2. recovery checkpoints for Aster Agent, Home Assistant configuration/component
   and the Bedroom Remote client;
3. a source-local `HA-Bedroom` key and the exact outbound-only HA-to-gateway
   path, without exposing the key;
4. an HA Bedroom row with `actions: []` and no content-volume profile;
5. installation of Bedroom's content-session publisher without widening its
   stereo, Wi-Fi or equipment-control contracts;
6. proof of volatile playback/class transitions, zero equipment commands,
   zero recorder history, restart/outage fail-closed behavior and full
   checkpoint rollback.

LG/CEC power, volume and mute remain a later independent physical-acceptance
decision. They cannot be inferred from this candidate.
