# Aster Home UI sounds

This private Kodi UI-sound resource uses short, low-level air puffs rather
than sharp pitched clicks or a sustained swish. Each has a rounded 14 ms
attack, two-stage low-pass filtering and a faded tail (80–95 ms total).
Left and Right are exact stereo mirrors weighted toward travel; Up is slightly
brighter and Down slightly warmer. Select, Back and notifications use related
centred puffs. Playback volume and passthrough are not adjusted.

Kodi's UI-sound contract maps actions to WAV files but exposes neither the
selected control's screen coordinates nor a runtime pan control. The stereo
weighting therefore communicates the remote command direction; it cannot make
the sound originate from each tile's exact position. All WAVs are original,
deterministically generated assets. Rebuild them with:

```sh
python3 tools/build_sounds.py
```
