# AsterTV Version 2 — resource and bedroom-client evidence

Updated: 2026-10-27. Status: qualified sizing estimate; final composed-client
measurement and a fresh N95 capture remain open.

## Purpose and evidence boundary

This record separates the resources needed to *run* AsterTV from the space used
to develop, checkpoint and recover it. It is not a purchasing guarantee. The
final bedroom recommendation must be checked against the release candidate and
the intended display, because 4K/HDR decoding and HDMI compatibility are more
important than idle CPU or memory alone.

The existing detailed assessment remains in
[Aster TV bedroom-client sizing](../reference/Aster-TV-Bedroom-Client-Sizing.md).
This page records the current release-gate conclusion without modifying that
working document.

## Fresh HP lab capture

The HP lab was measured read-only while Kodi and the Aster supporting services
were running:

| Item | Measured value |
|---|---:|
| CPU | Intel Core i5-9500T, 6 logical CPUs |
| Load averages | 0.08 / 0.10 / 0.11 |
| Installed memory | 16,439,242,752 bytes |
| Available memory | 15,417,921,536 bytes |
| Swap | none |
| Kodi resident memory | approximately 394 MiB |
| Camera proxy resident memory | approximately 20 MiB |
| Internal storage | 249,843,339,264 bytes total |
| Internal storage available | 245,167,546,368 bytes |
| Kodi add-ons | approximately 56 MiB |
| Kodi user data | approximately 411 MiB |
| Version 2 staging | approximately 434 MiB |
| Recovery checkpoints | approximately 1.44 GiB |

The staging and checkpoint figures are lab/recovery overhead, not a minimum
runtime requirement. Media is streamed from household services and is not
included in the client-storage estimate.

## Current bedroom-client estimate

The conservative deployment target remains:

- Intel N95/N100-class four-core x86-64 processor or better;
- 8 GiB RAM;
- 64 GB storage as a technical minimum, with 128 GB preferred for updates,
  logs and recovery headroom;
- gigabit Ethernet;
- an HDMI implementation proven with the intended display/receiver chain.

The previously tested N95 production-class box demonstrated 4K60 HEVC, HDR10
and AV1 playback. That evidence supports the processor class, but it does not
yet prove the final Version 2 composition on the same hardware.

Four GiB remains a plausible *pared-back 1080p* experiment, not the recommended
household target. Such a client should omit local voice work, read-along
generation, live camera viewing, very large Music shuffle queues and lab-style
recovery checkpoint retention. No 2 GiB target is proposed.

## Open verification

The N95 host now presents a different SSH host identity from the saved one.
That is consistent with a reinstall, but it must be confirmed at the console
before the saved host key is replaced. Host-key checking will not be bypassed.

After identity reconciliation, capture the same read-only resource set on the
N95 while the final Version 2 release candidate is idle and during representative
4K playback. Until then, the recommendation above is deliberately labelled a
qualified estimate.
