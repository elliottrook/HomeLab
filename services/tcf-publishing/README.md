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

## Initial private deployment

- `tcf-publisher` is unprivileged LXC 124 at `192.168.20.35`; the Content Desk
  listens on TCP 8080 and accepts ingress only from NPM `192.168.50.23`.
- `tcf-origin` is unprivileged LXC 125 at `192.168.20.36`; Nginx serves the
  visibly marked sample release on TCP 80 and accepts private validation only
  from NPM. It has no NAS, editor or AI path.
- Both guests use tracked default-deny nftables policies and report to the
  existing Beszel hub. Agent tokens are unique runtime secrets and never enter
  this repository.
- The sample release includes `MANIFEST.sha256`; HomeLab Doctor verifies it,
  service health, and primary plus independent guest-backup freshness.
- There is deliberately no public DNS, tunnel or route during A2/A3. Public
  launch remains subject to content, rights, font, mail and edge gates.
