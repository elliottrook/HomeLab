# Aster Speech

CPU Whisper STT and Kokoro-canonical TTS for Aster Companion. Piper is the
explicit degraded recovery path. Production runs in LXC 116,
`192.168.70.14:9130`, exposed under `https://aster.elliottrook.com/voice/`.
See [operator guide](../../docs/runbooks/Aster-Companion.md) for recovery and
[project evidence](../../docs/projects/completed%20projects/Aster-Companion-App.md) for acceptance.

- `/health`: service liveness, no credentials.
- `/v1/stt`: multipart `audio`, at most 15 MiB, temporary file only.
- `/v1/tts`: JSON `text`, at most 2,000 Python code points, WAV output.
- Both speech routes require the existing dedicated key or a valid Companion
  JWT with matching signature, issuer, audience and expiry.

TTS uses Kokoro ONNX `bm_daniel`, `en-gb`, speed `0.95` when its model and
voice-pack assets are present. If Kokoro cannot load or synthesize, the service
uses Piper as an explicit degraded recovery path and returns
`X-Aster-Speech-Engine: piper` plus `X-Aster-Speech-Degraded: true`; consumers
must not present that response as the canonical voice. Install the packages in
`requirements-kokoro.txt` and provision the model assets under the paths in
`speech.env.example` during the controlled deployment window.

`health_check.py` is a read-only, credential-free probe for liveness, HTTPS
routing, OIDC application discovery and JWKS reachability. Doctor invokes it
inside the speech guest. It does not replace a real user-login test.

The service runs as `aster-speech` with the checked-in systemd unit. The real
`/etc/aster-speech/speech.env` is `root:aster-speech`, mode 0640. The example
contains settings only. Back up the entire guest: Python venv, cached Whisper
model, Kokoro runtime and voice assets, Piper binary and voice files, unit and
protected environment are all needed for recovery. No audio history is needed.
Do not activate the example
with an empty key as an unreviewed deployment change.

Tests: `python -m unittest discover -s services/aster-speech -q` from the repo
with the service's Python dependencies installed. Tests substitute synthesis and
inference; the project evidence separately records real WAV/MP4 and restore tests.
