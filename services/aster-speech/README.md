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

`benchmark_stt.py` is the content-free M7 accuracy/latency harness. It records
fixture IDs, word-error counts and timings, never recognized text or audio.
The candidate keeps `base.en`, fixes decoding to English, disables cross-request
text conditioning and accepts an operator-reviewed vocabulary through
`ASTER_SPEECH_STT_HOTWORDS`. Treat that list as model policy: benchmark every
change against the frozen fixtures and real consented near/far-field samples.
Do not put private dictated text or open-ended conversation history in it.

`voice_candidate.py` is the repository-only M2 core. It owns the canonical
speech normalization and semantic-unit policy plus the bounded two-worker
scheduler. Without a separate batch renderer, both workers serve interactive
work and only worker zero may serve the lower-priority batch queue. When an
isolated batch renderer is configured, a third worker owns that backend and
both interactive workers remain dedicated to latency-sensitive speech. This
module is not production wiring and must remain side-by-side until the HTTP and
Wyoming adapters, real Kokoro renderers and LXC 116 gates pass.

`voice_protocol.py` defines the dependency-free `AVS1` streaming frame format:
a bounded JSON metadata header followed by bounded PCM payload bytes. Audio
frames declare request/unit order, sample rate, mono channel count and
`pcm_s16le`; streams finish with an explicit end, content-free cancellation or
content-free error frame. An explicit API cancellation completes the HTTP
stream with a `cancelled` frame; a disconnected client still cancels work and
propagates the transport cancellation.
`voice_candidate_http.py` exposes that contract as authenticated FastAPI router
factories for `/v2/tts/stream`, `/v2/batch/tts/stream` and their cancellation
routes. Caller class is fixed by the authenticated route and cannot be selected
in submitted JSON. The batch route accepts only its dedicated service key; it
does not accept Companion credentials or Authentik tokens.

`kokoro_candidate.py` verifies the approved asset digests before constructing
two distinct persistent ONNX sessions. Each scheduler worker owns one Kokoro
engine configured for two intra-op threads and one inter-op thread. The engine
returns bounded mono 24 kHz signed 16-bit PCM; the compatibility endpoint wraps
the same PCM in a WAV container without using a second synthesis path.
The listening-approved deterministic acknowledgement, `There, that's done.`,
is rendered once during startup and cached as PCM. Callers may request it only
after an action reports success; caching must never become speculative speech.

`aster_voice_candidate.py` and `systemd/aster-voice-candidate.service` are the
side-by-side candidate application and unit. They bind port 9131 and are not
referenced by the accepted production unit. Do not install or enable them until
the M3 backup, dependency, authentication and rollback gates are approved.
The candidate explicitly initializes the existing Whisper model because its
separate FastAPI lifecycle does not execute the legacy application's startup
hook. Direct pins are in `requirements-candidate.txt`; the exact added Kokoro
stack validated during M2 is in `requirements-kokoro.lock`. Deployments must
use the complete, M3-validated `requirements-candidate.lock`; resolving only
the direct pins allowed transitive drift during the first M3 preflight and is
not an accepted deployment path.

`vulkan_renderer_bridge.py` and `vulkan_renderer_client.py` keep the canonical
service boundary on LXC 116 while placing only synthesis compute beside the B60
in LXC 110. Kokopop remains bound to loopback. The bridge exposes one private
fixed-policy render operation: it requires a dedicated bearer credential,
accepts at most one normalized 240-character unit, and always selects
`bm_daniel`, speed `0.95` and WAV output itself. The LXC 116 client validates
mono 24 kHz/16-bit output before returning PCM to the existing scheduler and
caches only the already-approved acknowledgement. Neither request JSON nor a
caller can select the renderer URL, voice, speed or backend.

The candidate units are `aster-kokopop-candidate.service` and
`aster-vulkan-renderer-bridge.service`. The bridge environment example contains
settings only; the real shared renderer key must be independently installed as
root-owned mode 0640 files readable by the `ollama` account in LXC 110 and the
`aster-speech` account in LXC 116. Keep both units disabled until the private
listener, refusal, cancellation, contention and rollback gates pass.

The preferred isolated-GPU candidate is now the TrueNAS Arc A380. Deployment
files under `truenas/` build the exact pinned Kokopop revision, mount the
hash-verified model and bearer key read-only, keep Kokopop on an internal Docker
network, and publish only the authenticated bridge on the TrueNAS Servers-VLAN
address. `renderer.env.example` contains paths and the host render-group GID,
not secrets. Do not enable this stack or route LXC 116 to it until the narrow
LXC 116-to-TrueNAS firewall tuple and rollback have been approved and tested.
The approved canary tuple is only `192.168.70.14` to
`192.168.20.40:9132/TCP`; Kokopop itself remains internal to Docker. The
candidate service on LXC 116 may use this path while production port 9130
continues to use the retained renderer until listening and load gates pass.

The isolated News candidate uses `aster-kokopop-news.service` plus
`aster-batch-renderer-bridge.service` on LXC 114. Kokopop is loopback-only;
only the authenticated fixed-policy bridge binds `192.168.70.13:9132`. LXC 116
uses a renderer credential distinct from the News caller credential. Both LXC
114 units and the LXC 116 candidate remain boot-disabled until migration and
rollback gates are complete.
