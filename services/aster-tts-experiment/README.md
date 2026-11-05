# Aster TTS model experiment

This directory contains the fixed public/synthetic pronunciation corpus and
the fail-closed evidence tools for the bounded experiment documented in
[`docs/projects/Aster-TTS-Model-Experiment.md`](../../docs/projects/Aster-TTS-Model-Experiment.md).

The experiment deliberately has no deployment unit, listener, timer or
production route. `experiment.py prepare` imports the exact deployed
`voice_candidate.py` contract and records its hash, so the Kokoro control uses
the same normalization and 240-character semantic-unit policy as production.
Every renderer must produce two 24 kHz mono PCM16 WAVs per passage plus bounded
timing evidence. `record` rejects missing, malformed and implausibly paced
audio. `blind` verifies source hashes, normalizes loudness with ffmpeg and
writes a public playlist plus a separate private label mapping.

`render_kokoro_control.py` is intended to run transiently inside LXC 128. It
uses the installed, hash-verified `KokoroWorker`, records unit phonemes and
fails if the production voice service PID changes. It does not call or modify
the production endpoint.

`render_kokoro_reference.py` creates the fixed synthetic Kokoro reference and
matching transcript for Qwen Base voice cloning. It contains no human voice
sample or biometric voiceprint.

`render_qwen_candidate.py` verifies the pinned binary, talker, tokenizer and
synthetic reference before each run. It writes only a complete WAV or removes
the partial file, bounds stderr, fixes the sampling seed and records elapsed
time and input hashes. `--passage` and `--repeat` support the CPU screening
gate before a complete candidate run.
