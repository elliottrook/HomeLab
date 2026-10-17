# Aster Home UI sounds

This private Kodi UI-sound resource replaces the default sustained cursor
swish with short, low-level clicks. Left and Right are stereo-weighted toward
the direction of travel; Up is slightly brighter and Down slightly warmer.
Select, Back and notification events use related centred clicks.

Kodi's UI-sound contract maps actions to WAV files but exposes neither the
selected control's screen coordinates nor a runtime pan control. The stereo
weighting therefore communicates the remote command direction; it cannot make
the sound originate from each tile's exact position. All WAVs are original,
deterministically generated assets. Rebuild them with:

```sh
python3 tools/build_sounds.py
```
