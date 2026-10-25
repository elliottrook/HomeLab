# Aster canonical UI sounds

This private Kodi resource contains the owner-approved canonical Aster startup
sound and seven interaction sounds. The interaction family is derived from one
recorded CC0 mouse click. Every cue finishes at digital silence.

| Canonical sound | Kodi files | Use |
| --- | --- | --- |
| Up | `nav-up.wav` | Rising focus movement |
| Down | `nav-down.wav` | Falling focus movement |
| Left | `nav-left.wav` | Left-weighted lateral movement |
| Right | `nav-right.wav` | Right-weighted lateral movement |
| Boundary | `notify.wav` | Slower muted double pulse |
| Select | `select.wav` | Decisive click-clack confirmation |
| Back | `back.wav` | Retreating downward click |
| Startup | `startup.wav` | Layered sunrise chimes with a softened outro |

Kodi exposes separate filenames for each directional action. This revision uses
that capability: all seven navigation WAV files are distinct cues with a shared
source. The longer startup master is a separate soundscape.

All masters are deterministic 48 kHz stereo, 24-bit PCM WAV. Pitch shifting,
time stretching, layering, stereo placement and compact reflections are made
only from the same recorded mouse-click source. The canonical hashes and format
limits are pinned in `tools/build_sounds.py`.

Kodi maps actions to these files through `resources/sounds.xml`.

This source packaging does not deploy or reload the sound theme on a Kodi
client. Live adoption remains a separate checkpointed operation.
