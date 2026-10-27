# AsterTV Bedroom Client Sizing

> Status: Version 2 working assessment; not a purchase recommendation  
> Updated: 2026-10-26  
> Scope: a pared-back bedroom client using the same AsterTV/LibreELEC family

## Executive estimate

The current evidence supports an **Intel N95/N100-class four-core client with
8 GB RAM, 64 GB local storage and wired gigabit Ethernet** as the sensible
minimum target for a new bedroom deployment. Use 128 GB storage when the price
difference is small. This estimate assumes direct playback, hardware video
decoding and a reduced feature set; it does not assume software transcoding on
the television client.

Four gigabytes of RAM and 32 GB storage may be technically workable for a
deliberately reduced 1080p-only client, but neither boundary has been tested on
physical AsterTV hardware. They are therefore planning floors, not approved
specifications. The old Lenovo remains unqualified until it passes the same
playback, remote, restart and recovery gates.

## Measured clients

| Client | Relevant hardware | Measured result | Current limit |
|---|---|---|---|
| BOSGAME E3 Neo | Intel N95, four cores, Intel UHD, 16 GB RAM, 476.9 GiB NVMe, 1 GbE | LibreELEC 13/Kodi 22 loaded Aster at 3840×2160/60. Hardware-decoded 10-bit HEVC SDR, HEVC HDR10 and AV1 SDR samples at 40 Mbit/s played without GPU reset, memory pressure or rising load. | This was the lighter v1 family, not the complete v2 candidate. Current SSH host identity requires reconciliation before new live measurements. |
| HP ProDesk 400 G5 Mini | Intel i5-9500T, six cores, 16 GB RAM, 232.7 GiB storage | High-bitrate 83 Mbit/s 4K HEVC HDR10 direct play ran for 20 minutes with VAAPI, 99% queue, zero dropped frames and 36–38°C temperature. The complete v2 family passed mixed-player endurance and cold recovery. | Bench display path is limited to 3840×2160/30; this is a sink/path limit, not a compute limit. |

Current HP read-only baseline after the v2 endurance work:

- Kodi RSS 529 MiB; recorded high-water mark 777 MiB in the current process.
- Warm mixed-player runs settled around 622 MiB RSS after a 625 MiB peak.
- Earlier full-library shuffle construction reached roughly 1.0 GiB RSS; this
  is a build/queue stress case rather than normal idle playback.
- 14.3 GiB of 15.3 GiB RAM available, 33°C CPU and load averages below 0.4.
- `/storage/.kodi` occupies about 494 MiB. Lab-only retained checkpoints use
  about 1.33 GiB and staging about 301 MiB; a normal bedroom client should not
  carry the entire lab history.

Post-Acquisition Hub measurement on the same complete HP candidate:

- LibreELEC 12.2.1/Kodi remained active after more than three days of uptime,
  with no player open, load averages of 0.06/0.13/0.17 and both reported CPU
  thermal zones at 33°C.
- Kodi used 465 MiB RSS with a 631 MiB process high-water mark and 39 threads;
  14.3 GiB of 15.3 GiB RAM remained available without swap.
- The native Acquisition add-on itself occupies only 124 KiB. Adding the
  populated Media, Music and Books discovery surface therefore did not create
  a meaningful new client-capacity requirement.
- The current 495 MiB Kodi tree consists primarily of 168 MiB add-on data,
  163 MiB thumbnails, 68 MiB databases and 56 MiB installed add-ons. The Aster
  skin is about 13 MiB.
- Total `/storage` use was 4.1 GiB of 232.7 GiB. About 1.33 GiB of checkpoints
  and 301 MiB of staging are retained engineering evidence, not a deployable
  bedroom-client requirement. A release image should use bounded recovery
  retention rather than copying that history.
- After the corrected native action label was installed, five complete
  Media/Music/Books tab-switch cycles finished at 387 MiB Kodi RSS, a 580 MiB
  process high-water mark, 44 threads, 34°C and load 0.47/0.26/0.20. The
  request journal remained empty and Kodi logged no error. This supports the
  earlier conclusion that the Hub is not a new client-sizing driver.

Post-Books source-date activation measurement on the same HP candidate:

- With the complete 558-title Books catalogue active (505 ebooks, 46
  audiobooks and 7 podcasts), Kodi used 413 MiB RSS with a 599 MiB process
  high-water mark and 39 threads.
- 14.3 GiB of RAM remained available; load averages were 0.07/0.08/0.09 and
  the two reported thermal zones were 35°C and 33°C.
- `/storage/.kodi` remained about 496 MiB. The separately retained 1.33 GiB of
  checkpoints and 372 MiB of staging are lab recovery history, not runtime
  requirements.
- Populating every Books item with an authoritative source timestamp therefore
  made no meaningful change to the client-capacity estimate. The remaining
  sizing uncertainty is the complete v2 candidate on constrained hardware,
  not the catalogue shape on the HP lab system.

## Three useful boundaries

### Observed floor

The lowest fully identified physical client that has actually rendered Aster
and passed 4K60 hardware-decoded playback is the **Intel N95 BOSGAME with 16 GB
RAM**. That proves the processor/GPU class, not that 16 GB is required. It also
does not yet prove the final v2 family on that hardware.

### Recommended minimum

- Intel N95/N100-class four-core x86-64 system or better.
- Intel graphics with working LibreELEC hardware decode for HEVC Main10; AV1
  decode if AV1 is expected in that room.
- 8 GB RAM.
- 64 GB local flash/NVMe, preferably 128 GB for artwork-cache and recovery
  headroom.
- Wired 1 GbE. Wi-Fi is a fallback for ordinary 1080p material, not the
  qualification path for high-bitrate 4K remuxes.
- HDMI path proven at the room's required resolution, refresh, HDR and audio
  formats; a GPU feature claim is not enough.
- Supported USB-HID or Bluetooth remote with a recoverable keyboard/mouse path.

This tier should retain the full Aster interface, Jellyfin direct play, Music,
News, Books audio, the screensaver and read-only Home status. Camera live view,
large shuffle queues and heavy artwork refreshes should be tested together
before they are accepted as concurrent normal use.

### Comfortable specification

- Intel N100/N200/N305 or desktop-class 8th-generation Intel Core or newer.
- 8–16 GB RAM.
- 128 GB or larger SSD/NVMe.
- Wired 1 GbE and a known-good HDMI 2.0 path.

This provides room for the complete v2 family, larger artwork caches, recovery
packages, acquisition discovery, EPUB read-along and future voice-search
buffers without turning normal feature growth into a capacity exercise. The HP
i5-9500T/16 GB lab is above this client requirement and remains useful for
development rather than defining the minimum.

## Possible reduced 1080p tier

A 4 GB RAM, 32 GB storage endpoint may be evaluated only if it is intentionally
limited to 1080p direct play, ordinary stereo/DD audio, smaller artwork caches
and no retained lab checkpoints. Remove or cap whole-library shuffle, parallel
camera view, local narration generation, large recovery history and 4K/HDR
acceptance. Server-side TTS files may still be played because synthesis is not
performed on the client.

This tier fails qualification on any dropped playback, recurring buffering,
remote reconnect failure, storage pressure, inability to recover the profile,
or memory pressure during normal navigation. A slower initial catalogue load
alone is acceptable.

## What matters more than headline CPU speed

1. Hardware codec support and a working LibreELEC driver path.
2. Exact HDMI/EDID/HDR/audio compatibility with the room's TV or receiver.
3. Reliable wired network delivery for high-bitrate direct play.
4. Enough RAM for Kodi, artwork and bounded queue construction without swap.
5. A remote that reconnects after reboot and a recovery input method.
6. Reproducible install, profile backup and rollback.

Audio passthrough, HDR indication and CEC are path capabilities, not meaningful
CPU-sizing signals. A more powerful processor does not repair a receiver, EDID,
cable or missing CEC adapter.

## Final evidence still required

- Run the complete v2 candidate on BOSGAME and repeat idle, navigation,
  artwork, mixed-player and overnight memory measurements.
- Reconcile the changed BOSGAME SSH host identity before trusting further
  unattended measurements; do not bypass host-key verification.
- Test a deliberately memory-limited 8 GB configuration if firmware permits,
  or use a physically separate 8 GB endpoint.
- Qualify the old Lenovo with the same 1080p/4K, remote, network, restart and
  recovery matrix before calling it a bedroom option.
- Record wall power and fan/noise for any actual bedroom candidate.
- Revisit this estimate after M9's final page cleanup fixes the software shape.

The complete HP candidate now includes the credential-free Acquisition Hub
client, its populated discovery feeds and the bounded request journal. That
addition has passed the idle resource check above. It does not close M8 because
the requested low-end conclusion still needs evidence from the N95 production
class or another constrained endpoint, plus the final M9 software shape.

Until those checks are complete, **N95/N100 + 8 GB + 64/128 GB + gigabit
Ethernet** is a conservative engineering estimate, not a guaranteed shopping
specification.
