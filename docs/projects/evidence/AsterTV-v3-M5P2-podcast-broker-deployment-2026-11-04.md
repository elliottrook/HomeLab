# AsterTV v3 SA-M5P2 podcast broker deployment evidence

Date: 2026-11-04

State: inert queue broker deployed to Jen; UI not connected

## Recovery and first fail-closed attempt

The first install checkpointed `Media/appdata` as
`Media/appdata@aster-podcast-request-pre-20261105T033919Z`, then stopped with
`AUDIOBOOKSHELF_KEY_ISSUE` because a helper copied to `/tmp` could not resolve
Audiobookshelf's application-local Node modules. Inspection proved zero named
keys and no broker container. The entire failed target was preserved as
`/mnt/Media/appdata/aster-podcast-request-broker.failed-20261105T033919Z`.

The installer was corrected to set the exact `/app/node_modules` resolution
path for the issue/revoke helpers. No authority was broadened.

The successful retry checkpoint is
`Media/appdata@aster-podcast-request-pre-20261105T034101Z`. The exact OPNsense
pre-change backup is
`/conf/backup/config-astertv-jen-podcast-before-20261105-034234.xml`.

## Deployed boundary

- Container: `astertv-podcast-request-broker`
- Image ID:
  `sha256:edb996ebe0a74b4e60e63a3276fd7375adcdb437ca61d2c10a79610d42d79634`
- Base image amd64 manifest:
  `sha256:53739acebd52a300f19f52d93f2a6165f63300689bdf6f8af2bff0d63780e5e6`
- Runtime: UID/GID 65532, read-only root, all Linux capabilities dropped,
  `no-new-privileges`, bounded tmpfs and `unless-stopped` restart.
- Health: `{"execution_enabled":false,"state":"ready"}`.
- Audiobookshelf identity: one active named `AsterPodcastRequestBroker` API key
  tied to the existing restricted `user` account. The broker holds it mode
  0600; it has no update, upload or delete authority.
- Client identity: one independently revocable token bound to
  `AsterTV-Jen`/`jason`. The server retains only its SHA-256; Jen retains the
  token mode 0600.
- Firewall: rule `1b69df39-29d6-4d36-b382-fb3a255e22dd` permits only
  `192.168.1.180` to `192.168.20.40:8790/TCP`. The loaded PF ruleset contains
  exactly that source/destination/port path.

All plaintext credential staging was removed from TrueNAS, the Audiobookshelf
container and Jen after installation. Secret and queue files are mode 0600;
their directories are mode 0700.

## Acceptance

- Fourteen repository tests pass after the deployment helper additions.
- Wrong client token returns HTTP 401.
- Authenticated search returns 20 bounded candidates without returning provider
  IDs or feed URLs to the client.
- One test-only queue record entered `pending_owner_approval`.
- Exact replay returned the same opaque request and `duplicate=true`.
- Request reference evidence is retained only as SHA-256
  `1062711ccddd05569ca89d386141126d7b3329eb9e1b8ec99b3c73621a3516eb`.
- Container restart preserved status and idempotency.
- Deliberate broker stop made the path unavailable while Kodi stayed active.
  Restart restored health and the same queued state.
- Audiobookshelf remained at seven podcast items before and after the test.
  No folder, artwork, feed or episode was created/downloaded.
- Audiobookshelf and Jellyfin containers remained running; Jen Kodi remained
  active.

## Remaining gate

SA-M5P3 may connect only Jen's accepted podcast request UI to search, queue and
status. It must preserve Books/Podcasts playback and Back/focus behavior, render
dependency outage without leaving the page, and never imply that a pending
owner request is already subscribed. Owner approval/subscription execution,
Family, Bedroom and release promotion remain excluded.
