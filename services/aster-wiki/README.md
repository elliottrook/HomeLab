# Aster Wiki and Knowledge Mirror

This directory contains the implementation and reproducible seeds for the
private `homelab-wiki` and `aster-knowledge-mirror` repositories.

The Milestone 1 prototype has no third-party runtime dependency. Start it with:

```sh
python3 -m aster_wiki.app --wiki-root seed/homelab-wiki --port 8787
```

Then open `http://127.0.0.1:8787/`. Preview is read-only. Accept writes a
validated candidate beneath `state/candidates/`; it never edits the accepted
manifest or corpus directly.

The source dashboard at `/sources` shows accepted state, the latest bounded
pipeline result and queued controls. Per-source history pages compare retained
input hashes without exposing source content. Exact fetched bytes are retained
content-addressed beneath the protected collector state tree; normalized
human-readable copies remain the only generated corpus content.

Run the tests with:

```sh
python3 -m unittest discover -s tests -v
```

The seeds are copied into separate private repositories during deployment;
they are retained here so contracts, schemas and bootstrap content remain
reviewable with the HomeLab implementation record.

## Operator workflow

Open `https://wiki.elliottrook.com` and authenticate through Authentik. Use the
title and source ID to identify new equipment, then enroll its URL, Git document
or manual through the intake form. Preview does not mutate accepted state;
Accept creates a candidate for the collector and the accepted source becomes
the complete human equipment page.

The `/sources` dashboard shows queued work and bounded run history. Review a
quarantined item from its failure reason and preview, correct the source or
candidate, and retry it through the dashboard. Never bypass a validator. To
correct accepted material, update the authoritative source and let a normal
collector run create a new hash and retained original.

Operational checks on LXC 113 use the dedicated collector identity:

```sh
runuser -u aster-collector -- env PYTHONPATH=/opt/aster-wiki \
  python3 -m aster_wiki.cli status \
  --wiki-root /var/lib/aster-wiki/homelab-wiki \
  --state-root /var/lib/aster-wiki/state
runuser -u aster-collector -- env PYTHONPATH=/opt/aster-wiki \
  python3 -m aster_wiki.cli verify \
  --wiki-root /var/lib/aster-wiki/homelab-wiki \
  --state-root /var/lib/aster-wiki/state
```

Resume an interrupted run with `resume --run-id RUN_ID` and the same root
arguments. `rollback` restores the retained last-good accepted corpus. Mirror
rollback uses the retained `aster-knowledge-mirror.last-good` tree and should
be followed by `mirror-verify` before rebuilding Aster's snapshot.

Daily collection is owned by `aster-wiki-collector.timer`. The monthly
`aster-wiki-corpus-health.timer` writes a bounded report beneath
`state/reports/` and checks freshness, exact provenance, source links,
pipeline/input versions, duplicate claims and taxonomy coverage. HomeLab Doctor
reports missing, stale, warning or failed monthly state without exposing corpus
content.

Restore service in dependency order: recover the private human repository and
protected retained originals/state; verify the accepted corpus; rebuild and
verify the derived mirror; rebuild Aster's deterministic snapshot; then start
the intake and timers. Aster and the generated mirror are never authorities for
repairing missing human source material.
