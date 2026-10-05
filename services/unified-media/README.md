# Unified media book/audio foundation

This directory contains the reversible M1 shadow-stack definition for the
Unified Media Automation and Recommendations project.

It is deliberately separate from the production `new_arr` Compose project.
The shadow stack uses temporary ports and must not be started until the
project's protected checkpoint and single-writer gates are recorded.

## Services

- `lazylibrarian` — proposed acquisition authority for ebooks and audiobooks;
  it is not configured with indexers, download clients or credentials here.
- `audiobookshelf` — proposed Docker replacement for the current TrueNAS App;
  it reads the audiobook library and writes only its own metadata/config.
- `kavita` — proposed shadow ebook presentation and reading service. Calibre
  remains the metadata/conversion authority; Kavita is not permitted to edit
  Calibre's database.

## Storage contract

The production media dataset remains authoritative. The shadow stack uses the
same host dataset through a common `/data` path, but its ebook ingest path is
separate from the live Calibre library:

```text
/data/media/books             # existing Calibre library; never mounted into shadow services
/data/shadow/books            # disposable Calibre library copy for shadow validation
/data/media/audiobooks        # existing Audiobookshelf library
/data/ingest/books             # shadow ebook intake only
/data/downloads/books         # book download staging
/data/downloads/audiobooks    # audiobook download staging
```

No service in the shadow stack may directly write Calibre's `metadata.db`.
Calibre-Web Automated remains the sole planned writer after cutover, with
LazyLibrarian delivering files to the ingest boundary.

## Lifecycle

1. Create a protected export/checkpoint for the current Audiobookshelf App,
   Calibre-Web Automated config/database and Calibre library metadata.
2. Create a disposable ebook-library copy under the shadow state path; do not
   mount the production Calibre library into the shadow service.
3. Start the shadow stack on temporary ports with no acquisition credentials.
4. Validate Audiobookshelf library scan, users, playback and API access.
5. Validate Kavita health, library scan and ebook reading using a disposable
   test book or a
   copy, never the live library database.
6. Configure LazyLibrarian only after its provider and download-client scope
   is reviewed; first run is dry-run or a bounded selected title.
7. Cut over one service at a time and retain the source App/config until the
   restore gate passes.

## Port plan

The shadow defaults are intentionally distinct from the current services:

- Audiobookshelf: `30077`
- Kavita: `8284`
- LazyLibrarian: `5299`

Change ports only in an environment file outside Git. Private proxy, DNS,
Authentik, Homepage, Doctor and backup integration belong to later milestones
after shadow validation.
