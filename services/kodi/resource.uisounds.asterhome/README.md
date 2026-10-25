# Aster canonical UI sounds

This private Kodi resource contains the four owner-approved canonical Aster
interaction sounds. They share a quiet, dark, softly filtered character and
finish at digital silence.

| Canonical sound | Kodi files | Use |
| --- | --- | --- |
| Movement | `nav-left.wav`, `nav-right.wav`, `nav-up.wav`, `nav-down.wav` | Focus movement in any direction |
| Boundary | `notify.wav` | Unavailable action, edge and notification feedback |
| Select | `select.wav` | Short, low-pitched 560→440 Hz “tik” |
| Back | `back.wav` | Exact stereo-frame reversal of Movement |

Kodi requires separate filenames for each directional action, so the four
navigation files are byte-identical aliases of the single Movement master.
There are seven WAV files in the add-on but exactly four unique audio assets.

All masters are deterministic 48 kHz stereo, 24-bit PCM WAV. Movement and
Boundary use the accepted globally softened, half-volume “hhwoot” design. Back
is the accepted reversed Movement cue. Select is the accepted 105 ms lower
“tik.” The canonical hashes and format limits are pinned in
`tools/build_sounds.py`; running it validates the four masters and resynchronizes
the three Movement aliases.

Kodi maps actions to these files through `resources/sounds.xml`. It does not
expose focused-control screen coordinates to a sound resource, so all movement
directions intentionally use the same centred canonical cue.

This source packaging does not deploy or reload the sound theme on a Kodi
client. Live adoption remains a separate checkpointed operation.
