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

Live Aster Remote originally declared
`ASTER_REMOTE_VOICE_URL=http://192.168.70.14:9130/v1/stt`. A direct proposed
move to `192.168.20.37:9131` failed its connectivity preflight before any
checkpoint, environment change or service restart because LXC 104 has no
cross-VLAN route to LXC 128.

The existing private HTTPS proxy intentionally preserves:

- `/voice/` to legacy LXC 116 STT/rollback; and
- `/voice/v2/` to LXC 128's Mac-backed streaming TTS API.

No Mac-backed Remote STT location existed. The approved correction added
only `/voice/v3/` to LXC 128 with path preservation, then moved Aster Remote to
`https://aster.elliottrook.com/voice/v3/v1/stt`. It does not replace either
existing route or broaden the firewall.

NPM host 18 passed the exact predecessor dry run. A consistent SQLite backup
was written under
`/opt/nginx-proxy-manager/checkpoints/astertv-v3-m10-voice-proxy-20261106`
with SHA-256
`4b22da21c5c85d016c61ca746392d2c3552444393f6ca799af817a4baa9c1fbe`.
NPM rendered and reloaded successfully; `/voice/v3/health` then returned the
full canonical Mac authority while legacy `/voice/health` remained healthy and
the streaming `/voice/v2/` behavior remained unchanged.

The URL repair created checkpoint
`/var/lib/aster/checkpoints/astertv-v3-m10-mac-voice-20261106`, changed only the
declared voice URL and restarted only Aster Agent. The first end-to-end request
then correctly rejected LXC 104's legacy STT-only credential. A second
checkpoint,
`/var/lib/aster/checkpoints/astertv-v3-m10-mac-voice-key-20261106`, protected
the environment before a private mode-`0600` handoff aligned only the
restricted speech key. No credential value was logged or retained in transfer
storage, and every transient key/helper file was removed.

A fixed Qwen-generated synthetic “What time is it?” request through the public
Aster Remote endpoint returned HTTP 200 in 256.6 ms and matched the exact
expected normalized digest. The earlier macOS `say` fixture was rejected by
the Mac whisper bridge because of its audio encoding and is not counted as a
service failure. No fixture, response transcript or credential was retained.

## Regression controls

- `measure_speech_latency.py` requires host `aster-voice-prod`, the full
  canonical health identity, exact digest success and a 1.5-second p95.
- Aster Remote's source default names only the canonical HTTPS route.
- A dedicated NPM transaction validates host 18, the default upstream and both
  accepted predecessor locations before adding `/voice/v3/`.
- The Remote repair checkpoints its complete environment, changes only the URL,
  restarts only Aster Agent, validates both services and restores automatically
  on failure.
- A separate credential transaction accepts only a mode-`0600`, 64-hex
  restricted key, checkpoints the complete environment, changes only the named
  speech key, removes its handoff file in `finally` and restores on failure.
- The Family recovery materialization is regenerated from the corrected source,
  preventing a later fleet release from restoring the legacy default.

## Current gate

Canonical core and end-to-end Aster Remote speech both pass. The legacy route
remains available for bounded rollback; Aster Remote now uses only the
Mac-backed `/voice/v3/` authority.
