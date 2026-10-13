# Guarded Calibre worker

This is a one-shot worker definition for the unified media project. It is
profile-only in `compose.shadow.yaml` and does not run with the normal shadow
stack.

The worker accepts three explicit host paths:

- `UNIFIED_CALIBRE_LIBRARY_PATH` — the Calibre library to write;
- `UNIFIED_BOOK_INGEST_PATH` — bounded input, mounted read-only; and
- `UNIFIED_BOOK_OUTPUT_PATH` — conversion output.

The library variable is mandatory. The wrapper refuses the live
`/mnt/Media/media/books` path unless `ALLOW_PRODUCTION_CALIBRE_WRITE=YES` is
set explicitly. That override is reserved for a future cutover authorization;
it is not part of the shadow project.

The current validated primitives are:

```text
calibredb add --with-library /library /ingest/item.epub
ebook-convert /ingest/item.epub /output/item.azw3
```

Before production use, add duplicate/identity policy, metadata policy,
backup verification, a dry-run report and a rollback procedure. LazyLibrarian
must deliver into the bounded ingest directory; it must not receive direct
write access to `metadata.db`.
