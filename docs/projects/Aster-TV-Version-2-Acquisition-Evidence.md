# Aster TV Version 2 — Acquisition Hub evidence

Date: 2026-10-26

Status: approved album/ebook requests completed; both HP journal records committed;
bounded broker reply-parser correction active. Native duplicate-only UI review
remains after YouTube authorization releases the HP foreground.

## Boundary

The Acquisition Hub complements Seerr; it does not supply the playable landing
heroes. AsterTV receives only bounded, sanitized, unowned suggestions. Media
hands off to the established season-aware Seerr workflow. Music and Books use a
separate bearer token and exact provider identities, with two explicit presses
and a durable no-retry journal before any write.

No television stores a Seerr, Lidarr or LazyLibrarian credential. The restricted
broker owns those transports, re-reads the authoritative feed and revalidates
the exact MusicBrainz or Open Library identity immediately before a request.
An uncertain response is fenced and is never retried automatically.

## Reconciled live state

Read-only inspection found the Unified Media deployment had already advanced
beyond the earlier project note. These containers are running without restart
or OOM state:

- `unified-aster-seerr-broker`;
- `unified-recommendation-refresh-shadow`;
- `unified-recommendation-portal-shadow`; and
- `unified-lazylibrarian-shadow`.

The broker's mounted discovery directory and all five mounted credential files
are read-only. Its host port is bound only to `192.168.20.40:8788`. It has no
Sonarr, Radarr, Jellyfin, Docker or media mount. The running broker's four
acquisition/discovery modules and the refresher's producer module match the
repository byte-for-byte.

Fresh generated feeds at `2026-10-27T00:44:38Z` contain ten Media candidates,
three albums and twelve Books candidates. HP loaded all three from the live
authenticated endpoint rather than cache. Native 4K Media → Music → Books tab
navigation rendered the expected art, synopsis, status and request affordance,
then returned Home. No player opened, the request journal stayed empty and the
Kodi log gained no error or fatal event.

Provider-side read-only revalidation confirmed all three displayed albums are
currently requestable. The first displayed audiobook is already present in
LazyLibrarian despite the older discovery snapshot; the broker correctly
returns `available` for that identity rather than writing. Two displayed ebooks
are requestable. This proves why the second authoritative check must remain in
the request path.

## Original write gate (subsequently approved)

The first live Music/Books request remains deliberately unperformed. An album
request will add and monitor that exact release group in Lidarr and start its
missing-album search while leaving the wider artist unmonitored. An ebook or
audiobook request will add the exact Open Library work to LazyLibrarian and
queue only the selected format. Both can create downloader activity and files;
they are therefore not disposable in the sense of an automatically reversible
UI fixture.

Before M7a closes, the owner must approve the exact title or titles used. The
acceptance proof must capture first-press confirmation, one correlated provider
result, committed mode-0600 journal state, duplicate suppression and truthful
subsequent status. It must not delete or silently undo acquired media.

## Approved two-title trial — 2026-10-26

Jason approved Björk's *Homogenic* and the ebook *Heretics of Dune*, including
potential downloader activity and retention of any acquired files. Fresh feed
and provider checks matched these exact identities:

- album: `musicbrainz:release-group:810272e0-aef1-3d85-b2d3-e512e87fc38c`;
- ebook: `openlibrary:/works/OL893502W`.

The HP's installed model and request writer were exercised without changing
its foreground while the separate YouTube task awaited Google authorization.
First-stage confirmation sent nothing. The album's confirmed proposal sent one
HTTP request, returned `processing`, and committed its private journal. A repeat
submission returned the saved result without another send. Independent Lidarr
reads confirmed one exact album, monitored, with its artist unmonitored and
`monitorNewItems=none`. Its file count was zero at verification: this proves a
queued/tracked request, not a completed download or playable library item.

The ebook's initial request became uncertain during LazyLibrarian's synchronous
metadata import. A read-only database check found exactly the approved work and
title, with ebook and audiobook both `Skipped`. No add-book retry was made.
Inspection of the deployed API also established that `queueBook` returns the
literal plaintext `OK`; the broker's JSON-only transport rejected that valid
reply. The tested correction admits only that exact reply on LazyLibrarian's
queue operation, retaining strict JSON elsewhere.

The remaining queue step was then executed once through a staged copy of that
corrected transport. It made zero add-book calls. Independent API/database
readback confirmed ebook `Wanted` and audiobook still `Skipped`. The source-local
proof hash is
`72708ee6504892cd9cb5e04a3102f4141db5cec34fc1b13d735a1a202ae4851d`.
Only after that proof was verified did the HP reconcile this one uncertain
record to the confirmed `processing` result. Its original uncertain bytes are
retained. Two subsequent submissions of each title's proposal used the saved
result with zero network sends. Both records are mode 0600 inside the mode-0700
journal directory.

HP trial evidence is retained at
`/storage/.aster-staging/aster-acquisition-approved-trial1`:
`trial-result.json` preserves the original partial failure;
`queue-recovery.json` records the provider proof;
`heretics-uncertain.before.json` preserves the old uncertainty record; and
`reconciled-result.json` records both committed, duplicate-suppressed outcomes.
The uncertainty history was not erased or relabelled as an uninterrupted pass.

## Broker correction and deployment recovery

The shared TrueNAS broker now runs the corrected parser at source SHA-256
`73be0b582b15a353cc8747f36704df9ff6cc68ca0d25723916b9fd99ff986d0a`.
Its immutable image is
`sha256:e649732f3bc662d5d3f42afd00d010941011ea571d2108ed0c0a7bdf739584c1`.
An image-file comparison proved that only `aster_seerr_broker.py` changed across
the 22 files in `/app`. The first build from the shared context also included
an unrelated `refresh.py` change and was rejected for deployment. The accepted
image instead layers just the broker correction onto the preserved old image;
the Python/base layers are unchanged.

The full saved Compose file could not be replayed because its original
interpolation variables are absent. That attempt failed before recreation.
A broker-only candidate and rollback Compose file were therefore prepared from
the exact running contract. After normalization of environment ordering, all
environment values, command, user, working directory, entrypoint, healthcheck,
six read-only mounts, port binding, network and restart policy match the old
container. Only this broker was recreated. It is healthy, its health endpoint
returns HTTP 200, and fresh authenticated HP reads still return Media 10,
Music 3 and Books 12 candidates. No Kodi restart or UI change was made.

Private deployment checkpoint:
`/mnt/Media/appdata/dockge/unified-media-shadow/.aster-checkpoints/aster-acquisition-plain-ok1`.
It retains the old source, original Compose file, private live contract, exact
candidate/rollback service files, corrected source, image recipe and queue
proof. The original broker image remains tagged
`aster-seerr-broker:recovery-plain-ok1` at
`sha256:ff853b82fec2abb3cdbd60486fb64f91d035db30bce2e3c76f218829e5a40750`.
The shared build source and normal local broker image tag now name the accepted
correction. Other containers were not recreated.

For this broker's controlled operations, use the retained service-only Compose
file with project name `unified-media-shadow`; do not replay the full stack
until its missing environment inputs are reconciled. Rollback uses the retained
`broker-rollback.yaml` with the same project name and only the
`aster-seerr-broker` service. It restores code/image configuration, never the
provider database or HP request journal. The private files must stay outside
Git and ordinary logs.

All 110 Unified Media tests pass in normal and optimized Python. Native
UI acceptance remains a duplicate-only check: revisit these same journalled
titles, confirm the saved accepted outcome and verify no new provider request.
No further acquisition title or automatic retry is authorized by this trial.
