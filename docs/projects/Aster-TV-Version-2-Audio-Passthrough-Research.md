# AsterTV Dolby passthrough investigation — 2026-10-29

## Current safe state

Production `AsterTVProd` (`192.168.1.157`) is running v1.1.1. A read-only
inspection confirmed its saved Kodi normal output is `ALSA:hdmi:CARD=PCH,DEV=0`,
two-channel stereo, with `audiooutput.passthrough=false` and Sync Playback to
Display false. Jason has confirmed audible sound after this rollback. The
requested stereo state is already in effect; no production setting or service
was changed for this investigation.

The *saved but inactive* passthrough output selector points to HDMI 1, whereas
DRM and ALSA identify HDMI 0 as the connected `Beyond TV` route. That mismatch
is a concrete blocker to resolve before enabling passthrough, but Kodi's prior
selector persistence failures mean changing it without a checkpoint and live
receiver test could again break ordinary sound.

## Hardware and observed signal

Read-only DMI/PCI checks identify BOSGAME `Ecolite` / `E3 Neo`, Intel N95
(four cores), Alder Lake-N UHD GPU `[8086:46d2]` with `i915`, Intel PCH HD
Audio `[8086:54c8]` with `snd_hda_intel`, and BIOS `DNB20T V1.01`
(2025-10-10). The live OS is LibreELEC 13 nightly 2026-10-21, Kodi 22 RC1,
kernel 7.3.0. [BOSGAME's E3 Neo specification](https://www.bosgamepc.com/products/bosgame-e3-neo---n95-processor)
lists two HDMI 2.0 outputs and USB-C DisplayPort; the observed DMI and PCI
inventory, rather than that retail listing, govern this specific machine.

DRM reports HDMI-A-1 connected; the other HDMI and DP connectors are
disconnected. ALSA reports `Beyond TV` on HDMI device 3 (Kodi's HDMI 0).
The live ELD is present and valid, with AC-3 5.1, E-AC-3 7.1 and TrueHD
capabilities advertised, as well as LPCM and DTS. Linux describes ELD as the
attached HDMI sink's advertised audio capabilities in its
[ALSA proc-file documentation](https://docs.kernel.org/sound/designs/procfile.html).
This shows the PC receives Dolby capability information; it does not prove
the TV or downstream eARC/receiver will actually decode the stream.

In the previous bounded E-AC-3 production trial, sound played but the receiver
showed no Dolby indication and Kodi logged a PCM sink. Kodi's ALSA sink source
uses `AES0=0x04` for PCM and `AES0=0x06` for passthrough/non-audio
([source](https://github.com/xbmc/xbmc/blob/master/xbmc/cores/AudioEngine/Sinks/AESinkALSA.cpp)).
The lab HP, connected over DisplayPort to an LG display advertising only
stereo LPCM, also produced PCM in two short E-AC-3 trials. Those lab results
cannot validate a Dolby-capable output path. Both systems were restored to
stereo and playback stopped.

## Literature review and fit to this case

| Known concern | Source and applicability |
| --- | --- |
| Kodi may decode to PCM if output is Fixed, Sync Playback to Display is enabled, the selected output cannot carry a format, or the codec toggle is off. | [Kodi audio settings](https://kodi.wiki/view/Settings/System/Audio). Production is Optimized, Sync is false, and saved AC-3/E-AC-3/TrueHD flags are true; these simple causes do not explain the prior E-AC-3 failure. Global passthrough is currently off intentionally. |
| An Alder Lake-N N100 user saw PCM until enabling the individual Expert codec toggles. | [LibreELEC N100 report](https://forum.libreelec.tv/thread/29124-x86-64-audio-passthrough-not-working-on-a-n100-system/). Same symptom and similar CPU family, but production flags were enabled during the trial. |
| The HDMI port/path or stale driver state can hide E-AC-3, even when another output lists it. A fresh installation solved one Intel NUC report. | [LibreELEC Intel NUC report](https://forum.libreelec.tv/thread/29104-x86-64-eac3-passthrough-not-available/). Production's connected ELD *does* list E-AC-3, so it is not the same missing-capability symptom. Avoid reinstalling a working production system on this analogy. |
| Receiver/TV/optical routing may limit formats; EDID depends on the powered chain at startup. | [Kodi audio settings](https://kodi.wiki/view/Settings/System/Audio), [LibreELEC EDID guide](https://wiki.libreelec.tv/configuration/edid). The live ELD supports Dolby, but TV passthrough/eARC settings and actual receiver indication still need a physical test. Do not force an EDID override on the evidence so far. |
| Kodi with PulseAudio has separate sink-format and stereo-channel requirements. | [Kodi PulseAudio guide](https://kodi.wiki/view/PulseAudio). Kodi is launched with ALSA plus PulseAudio available, yet the observed trial used an ALSA sink. There is no evidence that PulseAudio caused this failure; disabling it blindly is unjustified. |

Most useful next test, when Jason can watch the receiver: checkpoint the
working v1.1.1 stereo settings and confirm playback is stopped; inspect Kodi's
live passthrough device list against HDMI 0/`Beyond TV`; select that connected
device while enabling only AC-3 and E-AC-3; play a known-format short clip;
check the Kodi ALSA sink for raw mode and the receiver display; then restore
stereo whether it passes or fails. If Kodi emits raw E-AC-3 but the receiver
does not indicate Dolby, inspect TV/eARC input mode, format forwarding and the
HDMI chain. If Kodi still emits PCM, investigate Kodi output selection and
capability negotiation on this OS before attributing the issue downstream.
