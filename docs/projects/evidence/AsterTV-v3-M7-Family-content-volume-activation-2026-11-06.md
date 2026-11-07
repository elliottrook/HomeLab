# AsterTV v3 M7 — Family content-volume activation

Date: 2026-11-06  
Target: `AsterTV-Family` and `Family Room Receiver`  
State: enabled and accepted for Family only

## Outcome

The owner approved the accepted playback receipt and activation of the Family
profile. The live Home Assistant configuration now contains only the reviewed
Family `content_volume` block. Bedroom remains unconfigured and has no volume
authority.

The enabled profile passed startup, bounded ramp, app manual override, gateway
outage, Home Assistant restart, next-session reset, no-history and Dolby
passthrough checks. Playback is stopped on Aster Media Home. The Onkyo is on,
unmuted and at the accepted Movie level `0.60`.

## Recovery and installed state

- Proxmox snapshot: `astertv-m7-family-volume-pre-20261106`.
- Exact configuration checkpoint:
  `/mnt/data/supervisor/homeassistant/.aster-checkpoints/astertv-v3-m7-family-volume-enable-20261106/configuration.yaml`,
  SHA-256 `251eac65…7a7c85`.
- Enabled configuration SHA-256: `f84f2400…547cfd`.
- Home Assistant configuration passed before restart and again after all tests.
- Thin-pool use was `30.23%` after the retained snapshot.

## Acceptance sequence

1. **Startup prime:** Home Assistant restarted while Family was idle at `0.44`.
   The controller consumed the existing idle state and made no adjustment.
2. **Dependency failure:** during the first Movie attempt, Aster Agent was
   observed inactive after an independent `systemctl` daemon-reload/clean-stop
   sequence. The bridge failed closed and the receiver remained `0.44`.
   Playback was stopped before Aster Agent was restored, preventing a delayed
   action. The gateway returned fresh idle state after recovery.
3. **Bounded Movie ramp:** the next Movie start produced the selected target
   `0.60`. Recorder rows show the 0.02-step ramp, including `0.48`, `0.50`,
   `0.52`, `0.54`, `0.56`, `0.58` and `0.60`; the component's controller also
   emits the preceding `0.46` step from the `0.44` baseline.
4. **Manual override:** one Aster Remote `equipment.volume_down` action changed
   the receiver to `0.595`. It remained there beyond a full bridge cycle; the
   controller did not fight the manual choice.
5. **HA outage/restart:** Home Assistant Core restarted while the Movie
   continued. After recovery, the controller primed at `0.595` and made no
   adjustment. `ha core check` passed.
6. **Next session:** after an idle transition, a new Movie session cleared the
   prior-session latch and moved `0.595 → 0.60`, proving normal automation
   resumed only on a new playback start.
7. **Passthrough:** during playback, the Onkyo reported input signal
   `Dolby Atmos`, listening mode `Dolby Atmos` and `5.2.4 ch` output. The
   controller never touched Kodi volume or audio routing.
8. **Privacy/final state:** Home Assistant recorder still contains zero rows
   with the playback schema in state attributes or event data. Kodi has zero
   active players and zero restarts; Aster Agent is active with zero restarts;
   window `10000` Media Home is restored.

The clean Aster Agent stop was not caused by the volume controller and became a
useful live fail-closed proof. The service was restored only after playback was
stopped. Its journal records the stop as a separate `systemctl` operation; no
volume action occurred while the gateway was unavailable.

## Retained boundaries

- Family targets remain Movie `0.60`, Television `0.58`, YouTube `0.455`,
  Music `0.43`, and Podcast/News/Book/Audiobook `0.44`.
- Maximum ramp step remains `0.02`; nighttime ceiling remains `0.60` using
  `sun.sun` exact states.
- Unknown, idle, paused, stale, malformed or unavailable state cannot adjust
  volume.
- Bedroom requires its own calibration, stereo/CEC proof, checkpoint and
  explicit activation.

Machine-readable receipt:
`services/kodi/astertv-fleet/releases/astertv-v3-family-content-volume-activation-2026-11-06.json`.
