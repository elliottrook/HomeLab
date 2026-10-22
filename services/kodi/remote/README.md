# Aster Home remote compatibility

`g20s-pro-plus.xml` is the profile-level Kodi keymap for the G20S Pro Plus
2.4 GHz USB receiver (`4842:0001`). The receiver reports its normal navigation
and media controls as Linux keyboard keys. Depending on its current mode and
wireless handshake, OK can arrive as keyboard Return or mouse-left; Back
arrives as mouse-right. The map changes only those controls:

- Return or mouse-left / OK routes known Aster dynamic lists to their bounded
  activation handlers and sends normal Kodi Select everywhere else;
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
