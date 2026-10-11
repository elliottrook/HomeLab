# Fotosforfun publishing service

This is the isolated append-oriented publishing core for Alisa's Fotosforfun
Desk. It is intentionally separate from `tcf-publishing`, whose fixed-slot,
complete-edition workflow is not appropriate for a growing gallery.

The initial code is local-only and uses synthetic test fixtures. It provides:

- versioned photograph records and immutable human approvals;
- soft retirement/reinstatement without deleting historical versions;
- deterministic active-gallery ordering;
- bounded image import with auto-orientation and metadata stripping;
- safe static rendering against the approved Fotosforfun template;
- complete checksum manifests and atomic release activation; and
- an audit ledger for publication and rollback; and
- a local-only Aster-style editor for add, edit, order, retire, approve and
  private-preview workflows.

No Authentik user, service, database, origin root, DNS record, firewall rule or
public route is created by this directory. Live provisioning begins only in A2.

Run the local tests:

```sh
python3 -m unittest discover -s services/fotosforfun-publishing/tests -v
```

Run the local editor against the approved export:

```sh
python3 services/fotosforfun-publishing/server.py \
  --state /tmp/fotosforfun-state \
  --template /path/to/approved/fotosforfun-export \
  --magick /opt/homebrew/bin/magick
```

It defaults to `127.0.0.1:8741`. Do not bind it to a LAN interface before the
A2/A3 service, reverse-proxy and Authentik controls are installed. The editor
intentionally exposes no live publish action during A1.

Deployment definitions are in `deploy/`. When creating tar archives on macOS,
set `COPYFILE_DISABLE=1`; the strict origin receiver treats AppleDouble `._*`
sidecars as unmanifested files and correctly rejects the release.

The accepted presentation source is the separate `sites/fotosforfun` Git
repository at commit `6a6c044ed3ce8197181e2ae68bbffa5a167a285e`. The renderer
requires that template's expected HTML hooks and does not silently invent a new
design.
