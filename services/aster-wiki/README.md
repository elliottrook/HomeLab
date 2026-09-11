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
