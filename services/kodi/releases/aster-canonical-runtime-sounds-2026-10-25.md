# Canonical AsterTV runtime sounds — 2026-10-25

Production and HP lab now share the approved canonical navigation sound family.
This is sound-only adoption, not promotion of the HP's version 2 interface.
Seven native filenames resolve to four cues; all navigation pages inherit the
existing resource theme and action map. No new list-boundary detection was added.

## Required runtime encoding

Keep source commit `4c283eaf0a35f34cf9018d06c27304cd09c760a5`'s PCM24 masters
unchanged. Their durations, levels, stereo balance and silences are approved.
Use lossless PCM32 copies in Kodi: every signed 24-bit sample is shifted left
eight bits, retaining exactly the same normalized amplitude and channel timing.
There is no normalization, resampling, dither, panning or sound redesign.

The initial exact-master trial installed correctly but failed native smoke with
`CActiveAESound::StoreSound - exceeded max samples`. Both boxes were restored
before compatibility copies were tested on HP and then deployed to production.
The rejected trial and its checkpoints remain retained, not accepted runtime.
Kodi Omega's [MakeSound allocation](https://github.com/xbmc/xbmc/blob/Omega/xbmc/cores/AudioEngine/Engines/ActiveAE/ActiveAE.cpp)
uses file size divided by decoded sample width; PCM24 decodes into 32-bit samples,
underallocating this buffer. The [StoreSound guard](https://github.com/xbmc/xbmc/blob/Omega/xbmc/cores/AudioEngine/Engines/ActiveAE/ActiveAESound.cpp)
reports the overflow. PCM32 avoids the mismatch without changing the signal.

Build a private deployment package with:

```sh
python3 services/kodi/package_aster_home.py --runtime-sounds --output /tmp/aster-runtime-release
```

The output must be new/empty. Without `--runtime-sounds`, packaging retains the
historical PCM24 source-reference archive: do not install that sound archive in
Kodi. The runtime manifest explicitly identifies the selected encoding.
Alternatively `v2/canonical_sound_compat.py --source <master-resources> --output
<new-directory>` creates original masters, runtime copies and a dual-hash manifest.

Runtime WAV SHA256:

| Cue / files | SHA256 |
| --- | --- |
| Movement / four nav aliases | `76cc78bb5b1c2901a0ceabd25c337daa51a4f1d04e828f94b8cc74e0f69c58ac` |
| Back | `9966043bb9601362f15e3f11f0272c78bad7f2c7201aee7952200c1c0aaef9a8` |
| Select | `19ffc9a9ea3d74e69c9e1b8a5ea3ca10ef8c6af8de47629b919609379226ad3e` |
| Boundary / notify | `5c9f60ac6e86b93beae0801646b9ba8b342e001a9b5fb47cfde3873786dcba80` |

## Acceptance and recovery

- Both native installs verified all seven hashes, exact predecessor backups,
  unchanged exposed settings and unchanged `sounds.xml`; theme reloaded without
  restarting Kodi. Neither playback nor volume/passthrough/display was changed.
- Both native engine smoke tests passed all four cues and six rapid Movement
  requests, zero sound-engine errors; no media/settings writes. HP artifact:
  `native-smoke-1792915104785055606.json`. Production artifact:
  `native-smoke-1792915153295973866.json`.
- HP final preservation `postcheck-1792915151728059058.json` verifies 48 Music
  members, 132 unchanged baseline members plus seven approved sound overrides,
  all current UI integrations, all 68 AV/language values and both database
  integrity checks. Players and queues empty, windows closed, no recovery fence.
- Per-box checkpoint: `/storage/.aster-checkpoints/aster-canonical-pcm32-20261025`.
  `verified.json` includes original/master and runtime hashes. Paired helper
  `deploy_canonical.py` supports guarded `rollback` only when idle and current
  assets still match; it refuses to overwrite newer changes. Run inside Kodi.
- Private extra recovery copies: `/tmp/aster-canonical-recovery-aNr4Hl/hp` and
  `/tmp/aster-canonical-recovery-aNr4Hl/production`; retained on-box checkpoints
  remain the primary durable recovery. Nothing was deleted.
- 497 v2 tests and 11 sound-family tests pass normally and under optimized Python.
  Exact sample equivalence, runtime archive contents, source hashes, deployment
  refusal/rollback and setting preservation are covered.

Physical listening through the receiver remains household acceptance: native
engine success is not a claim to have heard the receiver remotely. No Git push
or production version 2 UI deployment is included.
