# Aster TV Version 2 — Acquisition Hub live-gate evidence

Date: 2026-10-26  
Scope: HP lab Aster and the private Unified Media broker only  
Production BOSGAME: unchanged

## Outcome

The native Acquisition Hub release candidate is active on the HP lab. It
shows sanitized, unowned suggestions for Media, Music and Books. Film and
television retain the existing season-aware Seerr handoff. Album, ebook and
audiobook requests use a separate bearer capability and are revalidated by the
server before Lidarr or LazyLibrarian can receive an exact request.

No ARR credential is stored on the television. No acquisition was submitted
during deployment validation.

## Safety and recovery

- Unified Media checkpoint:
  `/mnt/Media/appdata/dockge/unified-media-shadow/.aster-checkpoints/acquisition-hub-20261026`
- Accepted pre-change Compose SHA-256:
  `7e37ace6465d37726fae0b0ed7a6d703860423c4e42953a3fb97f1345f819c89`
- HP first activation checkpoint retained at:
  `/storage/.aster-checkpoints/aster-acquisition-page2`
- HP accepted release-candidate checkpoint:
  `/storage/.aster-checkpoints/aster-acquisition-page3`
- Accepted HP Home predecessor SHA-256:
  `39b10fcac446626d3decd89e22cd8dda95b5ee50f9b5de489cb5f67f579a0834`
- Active HP Home SHA-256:
  `8b3867e46ec38e8e43b0fb8177a63ca3f4efbdcbd502f6121cc489a857d4d83b`
- Accepted HP candidate manifest SHA-256:
  `188b5923527f62adb42a02c65c3d3848a73550fda0202eb94fdf1ccedd68815c`

The isolated candidate install/verify/rollback test restored the Home
predecessor byte-for-byte. The first HP activation was also rolled back
byte-for-byte before the Kodi-native add-on activation candidate was installed.

## Verification

- Unified Media: 109 tests passed in normal Python and 109 with `-O`.
- Kodi v2: 1,177 tests passed in normal Python and 1,177 with `-O`; the one
  existing Mac-only skip remained unchanged.
- Broker and refresher containers are healthy after bounded recreation.
- Legacy `/health` remains HTTP 200.
- The Seerr token is rejected by the Music/Books write route, and the
  Acquisition token is rejected by discovery/Seerr routes.
- A malformed authenticated Acquisition request returns bounded HTTP 409 and
  performs no provider write.
- Lidarr and LazyLibrarian credentials passed read-only provider checks.
- HP fetched all three feeds over the live private path: 10 Media, 3 Music and
  12 Books items at validation time.
- Every exposed item was unowned and had `primary_action=request`.
- Kodi discovered and enabled only `script.asteracquisition`; the native window
  loaded without a Python or skin error, and exact active verification passed.
- The request journal remained empty during deployment validation.

## Findings resolved during the gate

1. Coordinator exceptions now terminate as bounded HTTP conflicts rather than
   closing an individual connection.
2. An expired optional Audiobookshelf reader token no longer prevents new
   discovery feeds. The refresher preserves the last good auxiliary snapshots
   and continues publication without changing that credential.
3. Music discovery seeds now resolve to exact, unowned MusicBrainz release
   groups; owned seed albums no longer produce an empty Music page.
4. New add-ons are enabled through Kodi's restricted JSON-RPC boundary rather
   than by modifying its database.

## Remaining acceptance work

- Visual and remote-control review of the three Hub tabs on the HP.
- One explicitly chosen disposable Music or Books request, only if an
  end-to-end provider-write trial is still desired. The deployment itself did
  not create, delete or retry any provider request.
- Production promotion remains a separate approval gate after HP acceptance.
