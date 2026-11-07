# AsterTV v3 M7 — Bedroom content-state disabled rollout

Date: 2026-11-06 (America/Vancouver)  
Target: `AsterTV-Bedroom` / `192.168.1.140`  
Outcome: content state live; equipment and automatic-volume authority absent

## Authorized boundary

Jason authorized the already-pushed, checkpointed Bedroom disabled-first
rollout after both Bedroom and Family were confirmed idle. The effect was
limited to:

1. adding a private `HA-Bedroom` identity to the accepted Aster gateway with
   `actions: []`;
2. converting Home Assistant's single accepted Family bridge to a two-room
   form while preserving every Family entity, action and volume value; and
3. installing only the Bedroom content publisher service and session helper in
   its live and boot-stable Remote trees.

The rollout did not add a Bedroom `content_volume` profile, equipment action,
physical-key mapping, account value or media identity.

## Recovery and transaction behavior

The retained recovery points are:

- Aster gateway/environment:
  `/var/lib/aster/checkpoints/astertv-v3-m7-bedroom-content-20261106`;
- Home Assistant configuration/contract:
  `/mnt/data/supervisor/homeassistant/.aster-checkpoints/astertv-v3-m7-bedroom-content-20261106`;
- Bedroom live/stable Remote service and manifest:
  `/storage/.aster-checkpoints/astertv-v3-m7-bedroom-content-20261106`.

The first two Home Assistant attempts exercised the rollback path. The first
successor health test incorrectly expected the CLI to print a `running` token;
the second treated Home Assistant's normal unauthenticated HTTP boundary as a
failure. Both restored the exact configuration and contract predecessors and
restarted Core. The corrected check used the container's actual running state,
then retained the successor only after `ha core check` passed. No partial
configuration survived either failed attempt.

## Installed state

| Owner | Installed object | SHA-256 |
|---|---|---|
| Aster Agent | content-capable gateway | `a804c06732b291275de830dcb0f8188ade5fc4fc3d0a557a86a742d1557cf1b3` |
| Aster Agent | private environment envelope | `4ed06d3c5c23e91ac0c49582668db3d74bbf8b01c0b999823bdee0109df77335` |
| Home Assistant | two-room configuration | `9bd3886236e57816bb4e2b233fcf124f4139a73d978b9479f8e8ceb0c9777b99` |
| Home Assistant | empty-actions-capable contract | `2c927737a82312c4fa9707d980a9c2bb3b92ff974d8cbce929c52249d87be82a` |
| Bedroom | Remote publisher, live and stable | `b443edc794f86fc66b1c92d46a048ed18871d9aa325835a2cb8b486d265415c3` |
| Bedroom | content session helper, live and stable | `a85f477bc877f835d18a7027c7532fcbacdd3ff932912a976bdb5a0b5cfd8acb` |
| Bedroom | stable Remote tree manifest | `07e493972f8f841da77163b89843b231ba6ea31eef864a6acbca8dd8943cb4cc` |

The sanitized gateway contract reads exactly:

- `HA-Family` / `family`: the accepted six power, volume and mute actions;
- `HA-Bedroom` / `bedroom`: `actions: []`.

Home Assistant preserves the accepted Family `content_volume` profile and has
no Bedroom `content_volume` block. Its two outbound long polls are established
from the Home Assistant host. Aster Agent, Home Assistant and both Kodi clients
remain active with zero observed restarts.

## Disabled-first proof

- An authenticated, source-local probe returned only sanitized Bedroom state:
  `available=true`, `room_id=bedroom`, `playback_state=idle`,
  `content_class=Unknown`, `page_id=media`, `sequence=35`.
- The response did not expose a title, path, filename, plot, account or other
  media identity.
- Home Assistant recorder contains zero state-attribute rows and zero event-data
  rows containing the playback schema.
- Bedroom's Remote live and stable trees match, its stable manifest matches its
  stable tree, and the enabled boot-time apply unit retains that tree.
- Bedroom Kodi is active, has zero restarts and zero active players. Family is
  also active, has zero restarts and zero active players.
- Wi-Fi, stereo/passthrough, LG/CEC, display and navigation settings were not in
  the changed-file set.
- All transient candidate, key-transfer, probe and observation files were
  removed. Private keys and retained checkpoints were not printed or removed.

## Regression and composition note

The exact deployment candidate passed 9 focused installer tests, 20 Home
Assistant tests, 38 Remote tests, 54 fleet tests and 14 tests in Aster's pinned
gateway runtime. A post-effect fleet compile and all 54 fleet tests pass.

The broader repository Remote candidate currently inventories an unused
`equipment.py` helper and a full-tree manifest for all clients. This bounded
Bedroom rollout intentionally installed neither: the running service imports
only `content_session.py`, and Bedroom has no equipment authority. A sanitized
live comparison therefore reports those two absent helper copies plus the
deliberately narrower manifest as expected candidate drift. It is not silently
promoted, copied or misreported as a clean full-composition deployment. The
next full Remote release must either remove that unused helper from desired
state or promote the complete reviewed tree under its own effect gate.

## Remaining gate

Bedroom playback/class transition remains untested. A later bounded acceptance
may start one known item, prove playing/class/freshness and return to idle while
confirming that no volume change occurs. Bedroom volume calibration and any
equipment authority remain separate owner decisions.
