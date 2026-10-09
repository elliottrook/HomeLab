# The Contrasting Frame publishing service

This directory contains the public-mirror-safe implementation for the private
Content Desk and static publisher. It intentionally contains no photographs,
licensed fonts, receipts, EULAs, private stories, approval records or secrets.

Runtime authorities:

- an allowlisted Immich collection on Synology supplies selected photographs;
- a scoped Synology directory supplies UTF-8 Markdown stories;
- private runtime storage holds workflow state and approved snapshots;
- the accepted Sites `dist/` export at commit `5b23ccb9` is the initial layout
  baseline; and
- a separate static-origin guest receives complete immutable releases only.

The initial deployment uses conspicuously labelled sample content. It must not
be promoted to the public domain. The publisher validates a frozen content hash
before scheduling or promotion. Editing any public field invalidates approval.

Run the dependency-free unit tests with:

```sh
python3 -m unittest discover -s services/tcf-publishing/tests -v
```

Generate or verify the accepted-baseline manifest with:

```sh
python3 services/tcf-publishing/manifest.py \
  /path/to/the-closet-fatman/dist \
  --verify services/tcf-publishing/accepted-dist.sha256
```

The commercial webfont is referenced only by checksum. Its bytes remain in the
private brand dataset and are injected into a release only after the licence
and domain gate passes.
