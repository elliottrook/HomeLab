# Aster Remote operations

## Service boundary

Aster Remote is the private iPhone PWA at
`https://aster.elliottrook.com/remote/`. The browser needs no login: the trusted
Nginx proxy passes the immediate client address and Aster Agent maps only
explicit household subnets to rooms. Aster Agent LXC 104 holds an in-memory
semantic command queue. Jen,
Family and Bedroom each maintain an outbound authenticated poll to TCP 9120.
There is no inbound television listener and the browser never receives a Kodi,
speech, Home Assistant or equipment credential. Each television retains an
independently revocable client key. Voice uses a separate STT-only server key
which the speech service does not accept for synthesis.

Trusted LAN `192.168.1.0/24` and the administrator-only Tailscale subnet-router
source `192.168.20.20/32` receive the household room set. The latter is needed
because iOS may keep the private subnet route active while the phone is also on
home Wi-Fi; Nginx then sees the router rather than the handset's Wi-Fi address.

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

Install on iPhone from Safari with **Share → Add to Home Screen → Open as Web
App**. On Android, open the same address in Chrome and choose **Add to Home
screen** or **Install app**. No App Store or Play Store package is needed.
While connected to an authorized home network, choose the controlled AsterTV
from the bottom room selector and use the touch surface or icon controls.
The app remembers the last valid room selected on that browser and restores it
the next time the PWA opens. This preference stores only the room ID; it does
not store credentials, searches, dictated text or Kodi input. If the room is
removed from the authorized room registry, the stale preference is ignored and
the first currently authorized room is selected. Clearing the browser's site
data resets the preference.

Voice recognition places cleaned text into Search. It does not submit
automatically: correct or append with the iPhone keyboard, then press Search.
More shows an editable Kodi field only while Kodi has requested non-sensitive
input. Password fields deliberately remain television-only.

If an older installed iPhone app shows the retired authentication flow, reopen
it once while online. Service-worker v6 takes control immediately, deletes the
old shell and removes the obsolete OAuth callback query. Do not restore the
old login JavaScript.

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
6. Aster Agent is active; direct `/v1/remote/session` access is HTTP 403 while
   the same request through private HTTPS on the trusted LAN is HTTP 200.

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
the direct-access 403 denial. After any restore or reinstall, run the probe and
then test one harmless Home action per room.

## Future Guest room

The network authorization map already reserves Guest VLAN `192.168.40.0/24`
for room ID `guest`, but no such client exists and no Guest firewall route has
been opened. The mapping therefore fails closed today.

When the fourth box arrives, enroll it with a new `AsterTV-GuestRoom` identity
and room ID `guest`. Only then add the narrow Guest-to-Nginx TCP 443 firewall
rule ahead of the RFC1918 deny. Do not permit Guest access to LXC 104, Kodi,
speech, Home Assistant or another AsterTV directly. Validate that a Guest
device sees exactly one room; household devices retain their separately
declared room set.
