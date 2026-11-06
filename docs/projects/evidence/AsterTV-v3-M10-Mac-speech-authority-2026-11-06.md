# AsterTV v3 M10 canonical Mac speech authority — 2026-11-06

## Outcome

Git and live read-only discovery confirm that canonical Aster Voice compute is
the M4 Mac mini behind the authenticated LXC 128 gateway. Its exact health
identity is Qwen3-TTS 1.7B Q8 Metal, voice-policy version 2, and whisper.cpp
`base.en` Metal. Six fixed synthetic STT rounds through that gateway were exact
and completed in 202.1–239.1 ms. No audio or transcript was retained or emitted.

The first AsterTV measurement followed the older V3 notes and reached legacy
LXC 116. That path remained accurate but took roughly 2.1–2.3 seconds because
its current environment selects `small.en`; it is diagnostic evidence only and
is not accepted as the V3 authority result.

## Integration drift and fail-closed result

Live Aster Remote still declares
`ASTER_REMOTE_VOICE_URL=http://192.168.70.14:9130/v1/stt`. A direct proposed
move to `192.168.20.37:9131` failed its connectivity preflight before any
checkpoint, environment change or service restart because LXC 104 has no
cross-VLAN route to LXC 128.

The existing private HTTPS proxy intentionally preserves:

- `/voice/` to legacy LXC 116 STT/rollback; and
- `/voice/v2/` to LXC 128's Mac-backed streaming TTS API.

No Mac-backed Remote STT location exists. The staged correction therefore adds
only `/voice/v3/` to LXC 128 with path preservation, then moves Aster Remote to
`https://aster.elliottrook.com/voice/v3/v1/stt`. It does not replace either
existing route or broaden the firewall. NPM apply and live Aster Agent repair
remain separately gated remote mutations.

## Regression controls

- `measure_speech_latency.py` requires host `aster-voice-prod`, the full
  canonical health identity, exact digest success and a 1.5-second p95.
- Aster Remote's source default names only the canonical HTTPS route.
- A dedicated NPM transaction validates host 18, the default upstream and both
  accepted predecessor locations before adding `/voice/v3/`.
- The Remote repair checkpoints its complete environment, changes only the URL,
  restarts only Aster Agent, validates both services and restores automatically
  on failure.
- The Family recovery materialization is regenerated from the corrected source,
  preventing a later fleet release from restoring the legacy default.

## Current gate

Canonical core speech latency passes. End-to-end Aster Remote speech remains
open until the additive proxy location and LXC 104 URL change are explicitly
approved, deployed and tested with the fixed synthetic phrase.
