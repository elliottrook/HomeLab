# Aster TV Version 2 — Acquisition Hub evidence

Date: 2026-10-26

Status: live read/discovery path accepted on HP; first Music/Books provider write pending owner approval

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

## Outstanding write gate

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
