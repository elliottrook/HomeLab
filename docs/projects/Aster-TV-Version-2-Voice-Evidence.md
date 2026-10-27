# Aster TV Version 2 — Voice search continuation

## 2026-10-26 — Recorder process boundary

Status: synthetic Mac and HP Linux checks passed; no microphone activation.

`voice_capture_runner.py` implements the process boundary previously missing
from the pure voice-search contracts. After the caller admits an explicit
press-to-listen session, it launches only the fixed `parec` argument vector for
the supplied exact source. It rejects monitor sources and does not select the
default device. PCM stays in memory; there is no audio file, shell, diagnostic
audio output or speech-service request in this adapter.

The recorder stops on button release or at a maximum ten-second wall deadline.
Its memory buffer rejects more than 320,000 PCM bytes, and short or odd-byte
recordings fail before speech transport. Cancellation discards the result,
including cancellation received while the process is shutting down. Cleanup
terminates and waits for the child, then kills and reaps it if necessary. Early
process exit and missing recorder/pipe are explicit unavailable outcomes.

Eight process tests use synthetic child processes, never audio hardware. They
cover release, deadline, cancellation after data arrives, excess output,
recorder failure, malformed PCM, monitor/pre-cancel refusal, and a child that
ignores termination. All eight pass on both macOS and HP Linux in normal and
optimized Python. The broader local voice test selection passes thirty tests
in both modes. HP test files are retained at
`/storage/.aster-staging/aster-voice-recorder1`.

This adapter is prepared code; it is not registered in the installed runtime or
bound to any remote button. Live voice search still needs the exact observed
microphone-button event, an available non-monitor capture source, the scoped
STT identity/transport and a visible listening/cancel integration. The current
YouTube device-authorization session retains foreground use of HP, so native
landing/search navigation checks are prepared but have not been run during
that session.

## Resume

Continue local assembly of the voice process/coordinator boundary or other
independent release work while HP's foreground is in use. When the physical
remote is available, verify its actual event/source identity before activating
capture. Never infer a microphone event from a generic product manual. Keep
the existing keyboard search route usable.
