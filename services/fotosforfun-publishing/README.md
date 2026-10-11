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
- an audit ledger for publication and rollback.

No Authentik user, service, database, origin root, DNS record, firewall rule or
public route is created by this directory. Live provisioning begins only in A2.

Run the local tests:

```sh
python3 -m unittest discover -s services/fotosforfun-publishing/tests -v
```

The accepted presentation source is the separate `sites/fotosforfun` Git
repository at commit `6a6c044ed3ce8197181e2ae68bbffa5a167a285e`. The renderer
requires that template's expected HTML hooks and does not silently invent a new
design.
