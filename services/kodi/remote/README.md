# Aster Home remote compatibility

`g20s-pro-plus.xml` is the profile-level Kodi keymap for the G20S Pro Plus
2.4 GHz USB receiver (`4842:0001`). The receiver reports its normal navigation
and media controls as Linux keyboard keys, but reports OK and Back as mouse
buttons. The map changes only those two buttons:

- mouse-left / OK selects the focused control;
- mouse-right / Back returns to the previous view;
- during full-screen video, OK opens the OSD and Back returns to the GUI while
  playback continues.

Install it as:

```text
/storage/.kodi/userdata/keymaps/g20s-pro-plus.xml
```

Restart Kodi after installation. Keep the remote's air-mouse mode disabled for
normal directional navigation. Removing the file and restarting Kodi restores
Kodi's default mouse behavior.
