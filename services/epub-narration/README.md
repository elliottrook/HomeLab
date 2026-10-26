# EPUB narration compiler

Repository-only M1 foundation for the
[EPUB Narration Compiler project](../../docs/projects/EPUB-Narration-Compiler.md).
It contains no real book text, audio, timing or progress.

The current modules establish four fail-closed contracts:

- `catalog.py` discovers Calibre EPUB rows through a SQLite read-only URI and
  rejects any source path outside the configured library root;
- `epub.py` extracts a bounded EPUB spine without executing content or allowing
  archive traversal;
- `state.py` persists the six-state generation lifecycle independently of
  Calibre; and
- `publication.py` validates an immutable manifest and atomically replaces a
  small ready pointer only after a complete generation is present.

`timing.py` records sentence cues as integer PCM sample indexes. It does not
invent word timing. Rendering and Opus encoding are intentionally absent until
the private 20-book benchmark milestone can use the pinned canonical Aster
voice and measure the real resource/storage envelope.

Run the synthetic suite:

```sh
python3 -m unittest discover -s services/epub-narration/tests -v
python3 -O -m unittest discover -s services/epub-narration/tests -v
```

Production invariants:

- mount the Calibre library read-only;
- keep state/work/output on a separate quota-bounded dataset;
- allow exactly one low-priority worker;
- publish only validated immutable generations;
- keep the prior ready pointer until a replacement is complete; and
- never log source text or store real generated artifacts in Git.

