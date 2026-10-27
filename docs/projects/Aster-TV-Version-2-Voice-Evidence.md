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

## 2026-10-26 — Single-attempt assembly

`voice_search_attempt.py` now joins explicit admission, the bounded recorder,
listening/transcribing presentation, scoped credential supply, speech wire
contract and normalized query return. Cancellation is checked before recording,
before credentials, before transport and before accepting a late transcript.
One attempt never retries. Recorder/transport failures show safe keyboard
fallback copy without exposing raw exception text. Audio, request and credential
objects are not retained in the returned session.

Six synthetic assembly tests cover success, pre-cancel, cancel after capture,
late speech response, one-shot transport failure and absent hardware. The full
local voice selection passes 36 tests in normal and optimized Python. The 18
assembly/coordinator/process tests also pass in both modes on HP Linux, under
the existing `/storage/.aster-staging/aster-voice-recorder1` staging directory.
These tests use only synthetic PCM and injected transports: no microphone,
real speech request, new identity, input binding or production change.

This closes the recorder-to-query assembly gap, not the live-device gate.
Actual remote event/source observation, restricted live STT transport and
Search's foreground listening controls are still required before activation.

## 2026-10-26 — Restricted transport and HP pilot assembly

The returned G20 receiver enumerates on HP as the previously measured HAOBO
`4842:0001` composite device. Its exact keyboard interface and dedicated
`aster_g20_mic` PulseAudio source are present; direct health from HP to the
existing private speech listener at `192.168.70.14:9130` returns HTTP 200.
Earlier physical evidence for this same endpoint records Linux
`KEY_VOICECOMMAND` 582 (`0x246`) and a successful local-STT phrase. The current
v1 keymap still contains an invalid symbolic `<select>` element, and the owner
observed the microphone control selecting the highlighted YouTube tile. The v2
candidate therefore uses explicit, distinct numeric mappings: 353 remains the
working Select dispatcher and 582 launches voice search. Voice is a no-op in
full-screen video, games and visualization so loudspeaker audio cannot
accidentally become a query.

`voice_search_transport.py` fixes the client to the private speech IP, port and
`/v1/stt` path, performs one request with no redirects or retries, bounds the
response and reads a root-owned mode-0600 credential outside Kodi add-ons.
`aster_speech.py` has a corresponding source-local key-file dependency accepted
only by `/v1/stt`; existing Companion credentials continue to work and the TV
key remains invalid for `/v1/tts`. No real credential has been created or read.

The HP add-on candidate opens the accepted grouped Search page before capture,
shows Listening/Working/error status in that foreground window, records only
while the admitted mic press is held, lets Back cancel, sends PCM only to local
STT, and passes the normalized transcript through a new `voice` command to the
same grouped-query function used by the keyboard. Audio and transcripts are
not written or logged. Two independent builds from the exact active HP
predecessors are byte-identical at manifest SHA-256
`2b6fb4740a57504b42f0ec54c1be0eb00fcf8499b3337021ab195d063930bf3b`.
The focused client suite passes 54 tests in normal and optimized Python; the
expanded package/policy selection passes 16 in both modes.

Activation remains deliberately gated. It requires a private checkpoint and
brief restart of the shared speech service to install the STT-only dependency,
a new independently generated key copied without disclosure to speech and HP,
and one idle HP Kodi restart for the add-on/Search/keymap candidate. A live
utterance is a separate immediate-consent step; neither prepared deployment
records microphone audio.
