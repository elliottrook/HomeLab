# AsterTV v3 M10 Jen synthetic HEVC gate — 2026-11-06

## Outcome

The standing Jen canary was idle with Kodi active before the test. A fixed,
privacy-safe 20-second 1920×1080/24 synthetic pattern with AAC audio was
generated transiently by Jellyfin's pinned FFmpeg, hashed as
`bec6556c61e2359d2e7f7c076b5639dfb57e69587cdce078e789545d4dac3c2c`
and staged only under Jen's private test directory.

Jen played eight two-second samples and reported:

- decoder `ff-hevc`;
- 1920×1088 at 24.000 fps;
- 76.0% progress before the bounded stop;
- 104.2% of one CPU core across the measurement; and
- a passing decode result with no surviving player.

The helper stopped playback in `finally`, Home was restored, and a separate
JSON-RPC check returned an empty active-player list. The fixture and helper
were then removed from Jen, local temporary storage, TrueNAS and the Jellyfin
container. The fixture contained no household media, title, account value or
credential. This reconfirms the already accepted Jen-only 1080p HEVC software
decode envelope; it does not generalize Jen's 1080p/stereo restrictions to
Family, Bedroom or the V3 release.

## Gate

The target-bound connected HEVC test passes. Sustained real-media and 4K
server-transcode evidence remains recorded in
`services/kodi/astertv-v3/low-spec/EVIDENCE-2026-11-04.md`.
