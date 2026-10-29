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

The validated HP/TCL path uses Kodi device
`ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH`. Its ELD advertises eight-channel PCM,
AC-3, E-AC-3, MAT/TrueHD, DTS and DTS-HD, but the real TV/eARC route wedged on
DTS-HD passthrough and remained silent until the receiver was rebooted. The
lab profile therefore enables AC-3, E-AC-3 and MAT/TrueHD passthrough, disables
DTS and DTS-HD passthrough, disables AC-3 transcoding, and uses the 7.1 channel
layout so Kodi can decode DTS sources to multichannel PCM. Codec switches must
follow measured end-to-end behavior rather than being copied from ELD alone or
blindly applied to another client or display path.

The reinstalled HP lab is currently connected by DisplayPort to an `LG HDR 4K`
display, not that earlier TCL/eARC chain. On 2026-10-29 its one valid,
connected ELD (`/proc/asound/card0/eld#2.3`) advertised **only two-channel
LPCM** at 32/44.1/48 kHz (`sad_count 1`, `sad0_coding_type LPCM`, speakers
FL/FR). ALSA maps it to `HDMI 0`/device 3. No AC-3, E-AC-3, TrueHD, DTS or
DTS-HD capability is exposed on this path. Kodi's normal output is HDMI 0
stereo and passthrough is off; dormant codec checkboxes in `guisettings.xml`
must not be treated as evidence that the current sink can decode them. Do not
copy the historical TCL passthrough profile to this LG path or use an EDID
override to claim surround support. To test passthrough, connect the lab to a
receiver/TV route that advertises the intended codecs, recheck the live ELD,
then use one known-format clip with a rollback checkpoint and physical receiver
indication. Preserve the audible stereo profile until that test succeeds.

Kodi's preferred audio language is `English` with "prefer default audio
streams" enabled. This selects an English stream when the source metadata
correctly tags one; content with missing or incorrect language tags still
requires manual selection.

