# Shared photography publishing service

This directory contains the public-mirror-safe implementation for one private
Content Desk and the static publisher used by The Contrasting Frame and The
Closet Fatman. It intentionally contains no photographs,
licensed fonts, receipts, EULAs, private stories, approval records or secrets.

Runtime authorities:

- an allowlisted Immich collection on Synology supplies selected photographs;
- a scoped Synology directory supplies UTF-8 Markdown stories;
- private runtime storage holds workflow state and approved snapshots;
- the accepted Sites `dist/` export at commit `5b23ccb9` is the initial layout
  baseline; and
- a separate static-origin guest receives complete immutable releases only.

Every content record, approval, schedule, asset root and release is bound to
either the `contrast` or `closet` site key. Builders must reject mixed-site
manifests. The Closet Fatman shares layout/content capacity, not the Contrasting
Frame brand package or licensed dearJoe font.

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
  listens on TCP 8080 and accepts ingress only from NPM `192.168.50.23`. Its
  approved private name is `tcf.elliottrook.com`.
- `tcf-origin` is unprivileged LXC 125 at `192.168.20.36`; Nginx serves the
  visibly marked sample release on TCP 80 and accepts private validation only
  from NPM. It has no NAS, editor or AI path.
- Both guests use tracked default-deny nftables policies and report to the
  existing Beszel hub. Agent tokens are unique runtime secrets and never enter
  this repository.
- The Content Desk stores append-only, site-scoped content versions and
  immutable approvals in owner-only SQLite state. Any edit creates a new
  version and leaves the current version unapproved. Deliberate cross-site reuse
  creates a separate unapproved record; it never copies approval.
- Drag-and-drop imports accept bounded UTF-8 Markdown and JPEG/PNG/WebP images.
  Original Markdown remains owner-only; the image pipeline auto-orients and
  strips metadata into a private JPEG preview. Imported files are scoped by
  site and content ID and do not become a saved content version until the user
  explicitly saves the draft.
- The private hostname is implemented by three internal resolver records,
  NPM host 36 and the owner-only Authentik application
  `photography-content-desk`. The direct TCP 8080 backend remains restricted to
  NPM, so DNS or URL knowledge cannot bypass the identity gate.
- The sample release includes `MANIFEST.sha256`; HomeLab Doctor verifies it,
  service health, and primary plus independent guest-backup freshness.
- There is deliberately no public DNS, tunnel or route during A2/A3. Public
  launch remains subject to content, rights, font, mail and edge gates.
