# Aster Remote operations

## Service boundary

Aster Remote is the private iPhone PWA at
`https://aster.elliottrook.com/remote/`. Authentik supplies a short-lived owner
session. Aster Agent LXC 104 holds an in-memory semantic command queue. Jen,
Family and Bedroom each maintain an outbound authenticated poll to TCP 9120.
There is no inbound television listener and the browser never receives a Kodi,
Home Assistant or equipment credential.

Current rooms:

| Label | Room ID | Client ID | Address |
|---|---|---|---|
| AsterTV Jen | `jen-lab` | `AsterTV-Jen` | `192.168.1.180` |
| AsterTV Family | `family` | `AsterTV-Family` | `192.168.1.157` |
| AsterTV Bedroom | `bedroom` | `AsterTV-Bedroom` | `192.168.1.140` |

The allowlist covers navigation, Home, context, Play/Pause, direct Aster Search
and active Kodi text input. Volume, mute and power remain unavailable until M7
installs explicit room-equipment authority.

## User operation

Install from Safari with **Share → Add to Home Screen → Open as Web App**.
Sign in with the existing passkey, choose the controlled AsterTV from the
bottom room selector, and use the touch surface or icon controls.

Voice recognition places cleaned text into Search. It does not submit
automatically: correct or append with the iPhone keyboard, then press Search.
More shows an editable Kodi field only while Kodi has requested non-sensitive
input. Password fields deliberately remain television-only.

## Health and diagnosis

Run the content-free probe directly:

```sh
python3 scripts/check-astertv-remote.py
```

HomeLab Doctor invokes the same probe. It fails on route/authentication drift,
a missing or extra room, inactive client add-on, non-private key mode, or a
live/stable/manifest mismatch. It does not require a client to be idle and does
not read key values, titles, typed text, playback history or account content.

For a disconnected room, check in order:

1. Kodi is active on that AsterTV.
2. `service.asterremote` is enabled.
3. The client can reach `192.168.70.10:9120`.
4. The client key remains mode `0600`.
5. Stable and live add-on manifests match.
6. Aster Agent is active and `/v1/remote/session` denies an unauthenticated
   request with HTTP 401.

Do not print the gateway environment or client key while diagnosing.

## Recovery and backup boundary

The gateway module, static shell, environment and checkpoints are protected by
the existing LXC 104 whole-guest backup and its Doctor age gate. Client code is
held in both the live Kodi add-on and host-bound stable custody and is fully
reconstructible from this repository. Client keys are intentionally not copied
into Git or general operator backups: loss of a physical client requires
revoking that identity, issuing a new independent key and re-enrolling it.

Accepted recovery points on 2026-11-05:

- Gateway room enrollment:
  `/var/lib/aster/checkpoints/astertv-v3-m8-rooms-20261105-r3`
- Gateway editable input:
  `/var/lib/aster/checkpoints/astertv-v3-m8-input-sync-20261105`
- Each room enrollment:
  `/storage/.aster-checkpoints/astertv-v3-m8-remote-<hostname>`
- Each room editable input:
  `/storage/.aster-checkpoints/astertv-v3-m8-input-sync-20261105`

Restore only through the matching installer/checkpoint contract. Confirm Kodi
is idle before any client restart. A gateway restore must retain Companion and
the unauthenticated 401 denial. After any restore or reinstall, run the probe
and then test one harmless Home action per room.
