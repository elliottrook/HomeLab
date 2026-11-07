# AsterTV v3 M11 — Bedroom promotion preflight

Date: 2026-11-07

Status: repository and silent live preflight passed; physical/display gate pending

## Safety boundary

This preflight was read-only on the live Bedroom appliance and its service
dependencies. It did not transfer or apply the candidate, restart Kodi or the
host, wake the television, issue an equipment command, capture camera or media
content, or read a credential value. The promotion runbook's display-available
gate remains closed, so no live release mutation is authorized by this result.

## Frozen candidate

Two independent builds produced 17 files and the identical tree digest
`eafb0ee6eb6cf0e65d3e6e9ee0245c8e3d59651a2e10cef26cca67f75b5ac9ce`.
The Bedroom artifacts remain exactly:

- bundle: `212ab2817fbe66fc6a38312968d0097ab2f967f636071b5040123cd6a78f7437`;
- plan: `e91bfd7a6d1d036ac4a4c428f7627ea7061fa6404c44489518f0670950ad3711`;
- guard: `5ea7d9b94b862351d0da45587bfae51218ac8090e0fcc8948d056bad80f1ea48`;
- SBOM: `e46b55d479b981b6fa402f32706e6d9d4984bb41c0e5759c2056040752641c21`;
- composition: `eab64fd2a4d67c54b9f89080ba410952ffabf237aeafd072f50709be2d9bb3b7`.

The bundle contains 73 safe-path members and no suspicious credential or
mutable-state filename. The existing immutable artifact freezes were not
changed.

The integrated local gate passed all 76 test files, scanned 93 candidate files
without a secret finding, and found zero conformance failures across 15 pages
and 127 focus controls. Its only open external gate remains the deliberate
non-author physical walkthrough.

## Live Bedroom baseline

- Exact identity: `AsterTV-Bedroom` at its pinned Wi-Fi address.
- LibreELEC nightly `20261021-440640e`; Kodi 22.0 RC1, Git
  `01d4146d5d251a0118b99a1de0d713395c93bd46`.
- Kodi was active and idle with zero active players and zero restarts.
- The current 535-file release guard passed; accepted-manifest SHA-256 is
  `474c887d0331267d7176795ba1fdc62f1a55c09baf4e86e3b031f75e69bcf204`.
- The accepted TV-series component manifest remains
  `aa589c8939b627aa19f9ec9b7abf9a0852eb3b33595b8c884e2b56f8ddb2dba0`.
- The Beszel 0.18.7 agent and Bedroom Wi-Fi stability unit are active with zero
  restarts; Wi-Fi power saving is off and the observed signal was `-54 dBm` at
  866.7 Mbit/s.
- More than 248 GB was free and 156 retained checkpoint directories were
  available. No checkpoint was created because no mutation began.
- HDMI remains the pinned `ALSA:hdmi:CARD=PCH,DEV=0` route with Kodi's 2.0
  room contract, passthrough plus AC-3/E-AC-3 enabled, and DTS, DTS-HD and
  TrueHD disabled.
- The official YouTube and Aster Search add-ons are enabled. The Books and
  Music surfaces are implemented through their accepted Aster components,
  rather than the nonexistent add-on IDs rejected by the probe.

## Content-free dependency checks

All checks returned service state or synthetic health only:

- Aster Remote: the full gateway, room, client and manifest parity check had
  already passed for Bedroom, Family and Jen.
- Audiobookshelf: container running and `/healthcheck` HTTP 200.
- Calibre-Web Automated: container running/healthy and local endpoint HTTP 302.
- EPUB narration: monitor timer active, state healthy, 167 sources observed,
  status 21,267 seconds old; Aster Speech active. No worker or Lab Hours action
  was requested or performed.
- Home Assistant: VM 103 running, guest agent responsive, `ha core info`
  returned exit 0 for Core 2026.9.1. The direct host HTTP probe is intentionally
  blocked by network policy and was not treated as failure.
- Jellyfin: container running, `/health` HTTP 200 and its restricted integrity
  identity authenticated successfully without exposing the key.
- Seerr and ARR: Seerr was running/healthy with zero restarts and its internal
  status endpoint passed; Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd were all
  running/healthy. The host-loopback Seerr port is intentionally not published.
- News Digest: UI active, health status OK, ingest and digest timers enabled,
  and briefing audio 95 minutes old.
- NetBox: its five required containers were healthy, the login redirected as
  designed through Authentik and the ingress was running.

## Remaining owner-assisted gate

The next step requires the Bedroom display/audio chain to be available and
playback stopped. Before the candidate is copied or applied, record the exact
physical Remote Volume Down, Volume Up, Mute and Power codes if they are not
already pinned. After the checkpointed Bedroom-first apply, prove one and only
one LG ARC/eARC CEC step, mute/unmute, power-off/on recovery, then agree the
Bedroom Movie, TV, YouTube, Music, News/Podcast, Books/Audiobooks and nighttime
maximum volume targets. Only then may the reboot, two normal-use runs and
acceptance marker complete the promotion.

