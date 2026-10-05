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
- `calibre-web` — proposed shadow ebook presentation and reading service.
  Calibre remains the metadata/conversion authority; Calibre-Web is not
  permitted to use the production database in this validation.

## Storage contract

The production media dataset remains authoritative. The shadow stack uses a
common `/data` path for the book/download staging tree, while the existing
audiobook library is mounted explicitly from its confirmed TrueNAS dataset
path and read-only:

```text
/data/media/books             # existing Calibre library; never mounted into shadow services
/data/shadow/books            # disposable Calibre library copy for shadow validation
/data/media/audiobooks        # existing Audiobookshelf library
/data/ingest/books             # shadow ebook intake only
/data/downloads/books         # book download staging
/data/downloads/audiobooks    # audiobook download staging
```

The Audiobookshelf shadow source is `/mnt/Media/media/audiobooks` on TrueNAS
(`UNIFIED_AUDIOBOOKS_PATH`), not the empty `/mnt/Media/data/media/audiobooks`
directory. This explicit variable prevents an accidental empty-library scan
and keeps the production audiobook files read-only to the shadow container.

No service in the shadow stack may directly write Calibre's `metadata.db`.
Calibre-Web is presentation-only. Because Calibre-Web Automated currently
stalls in its recursive ownership pass on this TrueNAS dataset, the eventual
single writer must be a separately evaluated Calibre import/conversion worker,
with LazyLibrarian delivering files to the ingest boundary.

The existing LinuxServer Calibre image is the current worker candidate:
`calibredb add` and `ebook-convert` have both passed against disposable paths.
The worker still needs a bounded ingest wrapper, duplicate handling, metadata
policy and backup/restore test before it can write the production library.

## Lifecycle

1. Create a protected export/checkpoint for the current Audiobookshelf App,
   Calibre-Web Automated config/database and Calibre library metadata.
2. Create a disposable ebook-library copy under the shadow state path; do not
   mount the production Calibre library into the shadow service.
3. Start the shadow stack on temporary ports with no acquisition credentials.
4. Validate Audiobookshelf library scan, users, playback and API access.
5. Validate Calibre-Web health, database loading and ebook reading using the
   disposable Calibre database copy, never the live library database.
6. Evaluate a dedicated Calibre import/conversion worker against a disposable
   library before changing the live single-writer contract.
7. Configure LazyLibrarian only after its provider and download-client scope
   is reviewed; first run is dry-run or a bounded selected title.
8. Cut over one service at a time and retain the source App/config until the
   restore gate passes.

## Port plan

The shadow defaults are intentionally distinct from the current services:

- Audiobookshelf: `30077`
- Calibre-Web: `8284`
- LazyLibrarian: `5299`

Change ports only in an environment file outside Git. Private proxy, DNS,
Authentik, Homepage, Doctor and backup integration belong to later milestones
after shadow validation.
