# Aster speech authority on the Mac mini

This directory defines the durable, hash-pinned Mac speech backend selected
after the November 2026 listening comparison.  The public and household API
boundary remains Aster Voice in LXC 128.  The Mac exposes no LAN listener:
Qwen3-TTS and whisper.cpp bind to loopback and a restricted, Mac-initiated SSH
reverse tunnel presents them as loopback ports inside LXC 128.

Accepted engines:

- TTS: `qwentts.cpp` 1.7B Base Q8 on `MTL0`, cloned from the synthetic Aster
  reference, fixed seed `20261104`, one concurrent request.
- STT: whisper.cpp `base.en` on Metal.  The LXC's existing faster-whisper
  model is retained as the explicit rollback implementation, not an automatic
  silent fallback.

`mac/run-authority.sh` is the LaunchAgent program.  It verifies every artifact
against `mac/artifacts.sha256`, verifies that Qwen and Whisper each use their
own complete durable library bundle through a relative `@loader_path` runtime
path, starts both model servers on loopback, registers the fixed voice, proves
health, then holds the restricted reverse tunnel. Any child failure exits the
supervisor so launchd restarts the whole coherent set. Temporary build paths,
symlinked libraries, missing libraries and unbundled non-system dependencies
fail closed before either model is loaded.

No model, executable, reference audio, private key or production secret belongs
in Git.  The accepted local root is:

`~/Library/Application Support/Aster Speech Authority/current`

Rollback is a route/configuration change in LXC 128 back to `onnx` plus local
faster-whisper; it does not depend on the Mac service being reachable.

