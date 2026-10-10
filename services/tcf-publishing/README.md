# Shared photography publishing service

This directory contains the public-mirror-safe implementation for one private
Content Desk and the static publisher used by The Contrasting Frame and The
Closet Fatman. It intentionally contains no photographs,
licensed fonts, receipts, EULAs, private stories, approval records or secrets.

Runtime authorities:

- an allowlisted Immich collection on Synology supplies selected photographs;
- a scoped Synology directory supplies UTF-8 Markdown stories;
- private runtime storage holds workflow state and approved snapshots;
- the accepted first-site export at commit `49f210c7` and completed Closet
  export at `c77684d` are the two current private layout baselines; and
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

`brand-sources.json` records the accepted source commits, private dataset paths
and annotation contracts without copying media or fonts into this public mirror.
The Contrast commercial webfont remains in its private brand dataset and is
injected into a release only after the licence and domain gate passes.

Both sites expose the same optional annotation fields. Contrast renders them as
a formal title with a fine antique-gold underline; Closet renders them as a
whimsical handwritten note and arrow. Annotation text and position are part of
the immutable approved payload, while the visual treatments stay brand-local.

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
- The site-scoped workspace list can create temporary records from the accepted
  old sample material. They are visibly titled `PLACEHOLDER`, retain
  `sample=true`, start with unknown rights/consent, and therefore cannot pass
  either the UI or server-side approval gate.
- An ordinary draft save cannot clear `sample=true`. Explicit promotion requires
  a saved imported photograph, replacement title and story, complete approval
  metadata, and the typed phrase `PROMOTE REAL CONTENT`. Promotion creates a new
  unapproved version; approval remains a separate human action.
- A fortnightly replacement snapshots every current website slot for one site.
  The edition cannot become ready until every snapshotted slot has either a
  changed, promoted and approved candidate or an explicitly confirmed removal.
  Slot removal is reversible while drafting and does not delete content history.
  Adding a website slot remains a separate structural action.
- The edition review manifest lists every slot as awaiting replacement, awaiting
  approval, approved or removed. It exposes no publish action and fails closed
  when no edition is active; the current public release remains independent.
- A ready edition can be rendered as an owner-only static candidate below the
  Content Desk. The renderer rechecks site isolation, immutable approval hashes
  and source-image SHA-256 values, writes a complete file manifest, and refuses
  stale or incomplete input. Candidate creation has no origin promotion path.
- Candidate rendering uses the accepted finished `dist/` template for its site,
  injects only approved images/stories and regenerated annotation/content data,
  and preserves navigation, brand assets and typography. It removes retired
  cards and refuses additions beyond the accepted template capacity. The current
  templates expose Contrast capacities 4/2/2/2 and Closet 2/2/2/1 across
  landscapes/flora/contrasts/people; making them identical requires a deliberate
  Closet layout revision rather than a backend assumption.
- Release preparation strips private-preview markings, verifies an exact file
  inventory and every checksum again, and derives an immutable ID from site,
  edition and manifest digest. Activation is a same-filesystem symlink exchange
  that returns the previous target for one-step rollback. The module is installed
  on the private publisher but is not connected to the origin or exposed in the
  GUI; public routing remains absent.
- The private hostname is implemented by three internal resolver records,
  NPM host 36 and the owner-only Authentik application
  `photography-content-desk`. The direct TCP 8080 backend remains restricted to
  NPM, so DNS or URL knowledge cannot bypass the identity gate.
- The sample release includes `MANIFEST.sha256`; HomeLab Doctor verifies it,
  service health, and primary plus independent guest-backup freshness.
- There is deliberately no public DNS, tunnel or route during A2/A3. Public
  launch remains subject to content, rights, font, mail and edge gates.
