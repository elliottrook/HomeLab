# M2 request-adapter contract

The recommendation portal remains a reader and approval surface. It never
calls Radarr, Sonarr, SABnzbd or download clients directly.

## Authorities

- Movies and television: Seerr search/request API. The installed Seerr
  `3.5.0` API requires an authenticated session cookie, so production use
  needs a dedicated private service identity and a protected session/renewal
  strategy.
- Music: Lidarr `3.1.0.4875` API with a narrowly scoped API key. The adapter
  resolves an unambiguous MusicBrainz/Lidarr album before a user-confirmed
  add/monitor/search action.
- Ebooks and audiobooks: LazyLibrarian wanted-item API. The shadow pilot uses
  a separate SABnzbd category and Calibre ingest boundary. Its API route is
  `GET /api?apikey=...&cmd=addBook&id=...`, but the selected Dune test exposed
  an upstream OpenLibrary tuple-binding failure, so the adapter remains
  disabled until a compatible metadata source is proven.

## Action contract

Every action receives a stable candidate ID, media type, authority, and
human-visible title/author/album evidence. Before mutation it must:

1. re-check the candidate against the authority;
2. reject an ambiguous or already-owned item;
3. record an idempotency key and dry-run result;
4. require the explicit approval action; and
5. record the downstream request ID and resulting state.

Failures are visible and retryable, but retries must reuse the same
idempotency key. The adapter tests must use mocked HTTP responses first, then
one explicitly selected live candidate per authority.

The initial implementation is in `authority_adapters.py`. Its transport is
injected, keeping credentials and cookies outside the planner while making
approval behavior testable. The Seerr and Lidarr paths have passed one live
bounded test each; LazyLibrarian remains an explicit blocked adapter rather
than guessing around the importer failure.
