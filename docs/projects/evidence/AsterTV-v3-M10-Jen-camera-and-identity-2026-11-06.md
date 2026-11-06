# AsterTV v3 M10 Jen camera and identity evidence — 2026-11-06

## Scope and standing canary authority

Jason designated `AsterTV-Jen` as the always-available V3 canary until V3 is
fully deployed in production. This permits bounded navigation, restart and
test use without a new conversational release request. It does not expand Jen's
1080p/stereo playback envelope to other clients, authorize destructive work or
waive the repository's per-push confirmation rule.

This slice repaired one false Home/camera account mismatch and measured one
12-second private camera session. No media was opened, no camera content or URL
was recorded, and the camera proxy remained loopback-only and on-demand.

## Root cause and correction

Jen's display marker was semantically correct, mode `0600` and bound to the
existing Jason recovery-admin mapping. The installed identity resolver hashed
the marker's raw JSON bytes. The original installer and later deterministic
fleet renderer serialized the same three fields with different whitespace, so
the unchanged identity produced a different subject. The account service
correctly failed closed with `identity-mismatch` and redirected the private
Cameras window to public News.

The resolver and M6 registry helper now validate the exact marker schema and
hash one canonical semantic serialization. Whitespace and key order no longer
change authority; missing, extra or changed fields remain invalid. Focused
tests cover compact, indented and reordered representations plus invalid
markers.

The Jen repair was exact-host, predecessor-hash and idle-player bound. It
checkpointed both live and boot-stable resolver copies, preserved the existing
registry and marker, and rolled back its first attempt when Kodi's account
service had not yet published state. The installer was then corrected to wait
for the service's non-empty state. The second run installed reviewed SHA-256
`6c7f1ae4…700900ef` to both copies and verified profile state `resolved`.

Kodi required its existing 25-second TERM fallback during each restart. The
fallback succeeded and Kodi returned active, but this remains a lifecycle
reliability observation rather than a clean graceful-stop result.

## Camera performance result

`services/kodi/astertv-v3/low-spec/measure_camera_stream.py` opened window
`11134`, selected its default Live control through JSON-RPC, sampled only host
counters and the loopback status shape, then left the page and restored Home.

| Measure | Result | Gate |
|---|---:|---:|
| Window activation | 130.9 ms | observational |
| Live-ready | 1,347.2 ms | 8,000 ms timeout |
| Frames observed | 4 in 12 s | at least 2 |
| Whole-host CPU used | 4.44% | at most 35% |
| Receive traffic | 116,388.75 B/s | at most 1,048,576 B/s |
| Transmit traffic | 4,314.42 B/s | at most 1,048,576 B/s |
| Kodi RSS growth | 26,848 KiB | at most 131,072 KiB |
| Peak temperature | 27,800 m°C | at most 75,000 m°C |

The result passed. No Kodi player appeared, `aster-camera.service` was inactive
after leaving Cameras, and the final window was Home (`10000`). This closes the
camera-stream-cost portion of M10. Artwork visibility, speech latency, broader
playback/failure suites and the non-author walkthrough remain open.

The complete repository gate then passed 67 local test files, the immutable-v2
check, 93-file secret scan, deterministic screensaver build, fleet compilation,
zero-gap operations audit and all 15 pages/127 focus controls. Jen's release
guard also reported its 534-file accepted set clean after the repair restart.
