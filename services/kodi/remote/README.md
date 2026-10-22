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

The power button is intentionally unmapped in the immutable v1.0.3 profile.
Aster Home v2 will capture its real event per client and may map a short press
to bounded system suspend only after USB wake, HDMI/audio/network recovery and
resume-state testing pass. Hardware that cannot pass will use an explicitly
labelled Display off fallback rather than pretending to sleep.
