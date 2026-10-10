# Aster Speech

CPU Whisper STT and Piper TTS for Aster Companion. Production runs in LXC 116,
`192.168.70.14:9130`, exposed under `https://aster.elliottrook.com/voice/`.
See [operator guide](../../docs/runbooks/Aster-Companion.md) for recovery and
[project evidence](../../docs/projects/completed%20projects/Aster-Companion-App.md) for acceptance.

- `/health`: service liveness, no credentials.
- `/v1/stt`: multipart `audio`, at most 15 MiB, temporary file only.
- `/v1/tts`: JSON `text`, at most 2,000 Python code points, WAV output.
- Both speech routes require the existing dedicated key or a valid Companion
  JWT with matching signature, issuer, audience and expiry.

`health_check.py` is a read-only, credential-free probe for liveness, HTTPS
routing, OIDC application discovery and JWKS reachability. Doctor invokes it
inside the speech guest. It does not replace a real user-login test.

The service runs as `aster-speech` with the checked-in systemd unit. The real
`/etc/aster-speech/speech.env` is `root:aster-speech`, mode 0640. The example
contains settings only. Back up the entire guest: Python venv, cached Whisper
model, Piper binary and voice files, unit and protected environment are all
needed for recovery. No audio history is needed. Do not activate the example
with an empty key as an unreviewed deployment change.

Tests: `python -m unittest discover -s services/aster-speech -q` from the repo
with the service's Python dependencies installed. Tests substitute synthesis and
inference; the project evidence separately records real WAV/MP4 and restore tests.

`benchmark_tts.py` is the M1 offline comparison harness. It runs the versioned
synthetic `tts_benchmark_fixtures.json` corpus through either current Piper or a
persistent Kokoro engine. Its JSON report contains fixture IDs, asset/fixture
digests, timing, RTF, RSS and declared thread settings, but no input text or
audio. Generated Piper WAVs are temporary and Kokoro audio remains in memory.
Run it only on an idle candidate or within an explicitly bounded test window;
the default five iterations are measurement work, not a health check.
Use repeatable `--fixture-id` arguments for a bounded latency or concurrency
probe without changing the versioned corpus or result schema.
`--intra-op-threads` and `--inter-op-threads` construct the pinned
`kokoro-onnx` 0.6.1 engine around an explicit ONNX Runtime session. This is for
M1 tuning because the package's public constructor does not accept session
options; candidate service code must wrap and test that behavior deliberately.

`voice_candidate.py` is the repository-only M2 core. It owns the canonical
speech normalization and semantic-unit policy plus the bounded two-worker
scheduler. Both workers serve interactive work; only worker zero may serve the
lower-priority batch queue, so News cannot occupy both interactive slots. This
module is not production wiring and must remain side-by-side until the HTTP and
Wyoming adapters, real Kokoro renderer and LXC 116 gates pass.
