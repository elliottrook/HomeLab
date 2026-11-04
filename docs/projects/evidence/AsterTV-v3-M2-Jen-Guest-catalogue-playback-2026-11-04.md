# AsterTV v3 M2 — Jen Guest catalogue and playback evidence

Date: 2026-11-04  
Target: `AsterTV-Jen` only  
Envelope: `SA-M2-JEN-GUEST`

## Outcome

Jen now has a separately revocable Guest path for the shared film and
television catalogue. It does not reuse Jason's Jellyfin session and it does
not expose personalized history, recommendations, favourites, downloads,
Music, Books, Requests, YouTube, Home, Cameras or Aster.

The retained client candidate is the deterministic r8 archive:

- SHA-256: `c745231223cca25c740923ad862250e6f6af2372628ccc94031f200650c5bc9d`
- final retained client checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m2-jen-guest-r10-retained-20261104`
- source pre-change checkpoint:
  `/mnt/Media/appdata/jellyfin/.aster-checkpoints/astertv-guest-pre-20261104`

This remains a Jen candidate, not a Family/Bedroom deployment or a v3 release.

## Source identity and permissions

The dedicated Jellyfin identity is `AsterTV-Guest`. Before retaining it, the
provisioner created and deleted a disposable identity and verified that the
user count and name collision returned to their original values. The final
identity was then recreated with the same bounded policy.

Allowed library folders are exactly:

- Movies
- Shows
- Archive Movies
- Archive TV

Playback, remuxing and required audio/video transcoding are enabled. The
policy denies administration, deletion, downloads, remote and shared-device
control, Live TV, user-preference changes and access to other libraries. The
system-generated Playlists view is not trusted as authority; the client
adapter allowlists the four folder identifiers above.

The independently revocable credential is held only at
`/storage/.aster-private/jellyfin-guest.json` with mode `0600`. Git contains no
credential. The account registry contains only an opaque
`local:jellyfin-guest:sha256:…` reference, and the identity resolver requires
the exact private credential plus the exact four library names.

## Client isolation

`plugin.video.asterguest` provides only the Guest catalogue flow:

- library to title navigation;
- movie details before play;
- series to season to episode to details/play; and
- bounded artwork, metadata and playback resolution.

Stream URLs presented to Kodi contain no Jellyfin token. A loopback-only relay
on `127.0.0.1:57321` resolves PlaybackInfo and allowlists HLS master, child and
segment requests. Its client envelope is H.264/AAC, two-channel audio, maximum
1920 pixels, 16 Mb/s video and 192 kb/s audio. InputStream Adaptive consumes
the relayed HLS route. Guest playback reporting is suppressed, so it cannot
become Jason's or another profile's Continue Watching state.

The profile authority grants only `guest_catalogue_browse` and
`guest_media_playback` to Guest. The normal Media route opens this adapter;
direct attempts to reach the other private AsterTV routes remain denied.

## Recovery proof

The exact retained client was rolled back to the pre-adapter r9 checkpoint.
The Guest add-on and authority mapping were absent after rollback. Reinstalling
the same hash-pinned archive exposed one clean-recovery gap: Kodi rediscovered
the add-on but did not automatically enable it. The installer now waits for
Kodi JSON-RPC, enables the exact add-on ID and verifies the resulting enabled
state. A second exact rollback/reinstall retained r8 under the r10 checkpoint
without manual enablement.

Source rollback was separately rehearsed by deleting only the newly created
disposable Guest identity and verifying restoration of the original user
count. The final source identity was retained by design.

## Acceptance evidence

After a cold Kodi restart:

- the Guest add-on was enabled and its loopback relay was listening;
- the Guest catalogue opened in the normal video window;
- a real film advanced to two seconds at playback speed 1;
- playback stopped and Kodi reported no active player;
- Guest `Played`, `PlaybackPositionTicks`, `PlayCount` and `LastPlayedDate`
  remained unchanged;
- the accepted-v2 guard reported `clean` across all 528 protected files; and
- no Jason credential or playback state was used.

Local verification passed:

- 29 account/authority tests;
- 7 Guest adapter/provisioning tests;
- 37 top-level v3 discovery tests;
- Python compilation for the changed modules; and
- deterministic candidate validation plus credential-pattern scanning.

## Deliberate exclusions

No change was made to Family, Bedroom, Jason's Jellyfin identity/session,
Jellyfin global settings, unrelated libraries, Music, Books, Requests,
YouTube, Home, Cameras or Aster. Promotion beyond Jen and all M3 work remain
outside this completed envelope.
