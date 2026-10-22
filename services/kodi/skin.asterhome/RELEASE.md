# Aster Home 1.0.0 release candidate

## Status and boundary

Aster Home 1.0.0 is the first owner-accepted **private production candidate**
for the Kodi interface. Its complete interface and normal Mac Kodi workflows
have been exercised against the household libraries. It is not yet the
production-appliance release: physical LibreELEC testing must still prove 4K,
HDR10, receiver audio passthrough, sustained playback, Bluetooth/USB-HID remote
control, reboot recovery and acceptable performance on the selected endpoint.

The skin uses a 1920x1080, 16:9 Kodi design canvas. Kodi scales that canvas to
3840x2160 output. Kodi renders video separately at the source/output mode, and
library fanart can retain its native resolution. Aster's right-sized raster UI
assets may be replaced with higher-density approved exports later if 4K
inspection identifies softness; that does not require a second layout.

This is a private HomeLab release. The artwork licence/provenance recorded in
the README does not grant public brand redistribution or Kodi-repository
publication.

## Release bundle

Build with:

```sh
python3 services/kodi/package_aster_home.py \
  --output /path/to/aster-home-v1.0.0
```

The deterministic bundle contains four independently installable Kodi ZIPs
and `aster-home-v1.0.0-manifest.json`. It also declares one external official
Kodi dependency, `plugin.video.youtube` 7.4.4; third-party source is not
vendored into the private bundle:

1. `plugin.video.asterhome` — combined movie/TV genre directories.
2. `plugin.audio.asterbooks` — loopback-only Audiobookshelf playback bridge.
3. `resource.uisounds.asterhome` — optional directional Aster clicks.
4. `skin.asterhome` — the v1 interface.

Install YouTube 7.4.4 from the official Kodi Omega repository, then install
the two private plugins, sound resource and skin. Kodi may resolve YouTube
automatically from that repository because the skin declares it as a required
dependency, but confirm its installed version before enabling Aster Home. Use
Kodi's **Add-ons → Install from ZIP file** workflow. Select **Aster Home** under
**Settings → Interface → Skin**. Select **Aster Home UI Sounds** separately if
the directional click set is wanted.

The official YouTube add-on renders its root catalogue without credentials,
but Data API routes such as Trending and search require an owner-created
YouTube Data API v3 key. Account features additionally require the owner's
OAuth client and interactive sign-in. Follow the add-on's maintained key guide
at `https://ytaddon.page.link/keys`, store the resulting values only in that
client's YouTube add-on settings, and never add them to this repository or the
release archive. Aster does not provide, proxy or share Google credentials.

The package deliberately excludes tests, build tools, pilot publishers,
source SVGs, caches and developer documentation. It contains no API key,
password, profile database, Kodi library database, watched-state database or
generated household feed.

## Client state and normal operation

The following state belongs to each Kodi client and is not part of the release
ZIP:

- Jellyfin add-on installation, authentication and synchronized Kodi library;
- Audiobookshelf bridge configuration under the audio add-on's `addon_data`;
- Aster Books, Home and Digest feed snapshots under the skin's `addon_data`;
- generated media filters and local Kodi GUI/region/audio settings;
- YouTube add-on settings, Google API/OAuth credentials, sign-in and history;
- the optional private camera bridge; and
- the selected UI-sound preference.

Use a 24-hour Kodi regional clock. Audio passthrough, display refresh-rate
switching, HDR and resolution are endpoint settings and must be chosen during
the physical test rather than embedded in the skin.

If a feed is absent or stale, the corresponding page must fail closed or show
its bounded unavailable state; do not insert credentials into skin XML, media
URLs or feed files. Audiobookshelf credentials belong only in the audio
add-on's mode-0600 configuration. Watch-state dots, checks, progress and series
counts are projections of Kodi/Jellyfin metadata, not a parallel database.

## Rollback

Before first physical deployment, back up the Kodi profile and retain the
previous accepted add-on directories. To roll back the interface, switch to
Kodi's Estuary skin first, then reinstall the previous Aster ZIP or restore the
profile/add-on checkpoint. Removing the skin does not alter Jellyfin media,
TrueNAS files, Home Assistant entities, Audiobookshelf media or watched-state
authority.

Abort physical promotion and retain the existing Apple TV if Kodi repeatedly
crashes, loses remote control after reboot, cannot restore the previous skin,
transcodes material expected to direct play, fails HDR10 or receiver
passthrough, or requires broader credentials/network access than documented.

## Physical production gate

- [ ] Boot and restart LibreELEC repeatedly without manual repair.
- [ ] Install and hash-check the v1 bundle from a clean client profile.
- [ ] Confirm the complete navigation path with the selected remote after
      pairing, reboot and idle reconnection.
- [ ] Verify 1080p and 4K direct play, refresh-rate switching and sustained
      playback without dropped frames or unexpected transcoding.
- [ ] Verify HDR10 through the television and Dolby Atmos/DTS passthrough
      through the receiver using known representative files.
- [ ] Verify subtitle/audio selection, playback OSD, watched state and resume.
- [ ] Verify YouTube search, account sign-in, subscriptions and 1080p60 /
      2160p60 playback; record dropped frames and test HDR separately.
- [ ] Exercise Music, Books/Audiobooks/Podcasts, Digest and Home failure states.
- [ ] Measure CPU, GPU, memory, temperature, network and UI responsiveness.
- [ ] Prove profile backup, Estuary fallback and Aster restore.
- [ ] Record accepted limitations and issue the project USE / CONDITIONAL USE /
      REJECT decision before replacing the Apple TV.

Until those checks pass, use **v1.0.0 production candidate**, not **production
appliance**, in operator records.
