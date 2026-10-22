# LibreELEC client configuration

These files are endpoint-specific deployment inputs, not Kodi add-ons. Apply
them only after confirming the target hardware exhibits the documented
condition.

## HP ProDesk 400 G5 HDMI audio

`modprobe.d/aster-hp-hdmi.conf` enables every Intel HDMI/DisplayPort codec pin.
It is required on the Aster lab HP ProDesk because its firmware reports the
active codec pins with connectivity `N/A`. LibreELEC otherwise logs `HDMI: pin
NID 0x5 not registered` and creates only the Conexant analogue PCM, despite a
valid connected display and an EDID containing audio descriptors.

Deploy to `/storage/.config/modprobe.d/aster-hp-hdmi.conf`, retain a copy of
any existing file, and reboot. Validation must show all of the following:

- `/sys/module/snd_hda_codec_hdmi/parameters/enable_all_pins` is `Y`;
- `aplay -l` includes `HDMI 0` with the connected display name;
- the connected `/proc/asound/card*/eld*` entry has both `monitor_present 1`
  and `eld_valid 1`;
- Kodi opens `hdmi:CARD=PCH,DEV=0` without falling back to the analogue sink.

Rollback by removing the deployed file, rebooting, and restoring Kodi's prior
audio device selection if needed. Do not use this override as a generic HDMI
fix: first prove that EDID advertises audio and that the codec pin is being
skipped.

