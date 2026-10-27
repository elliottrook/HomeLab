# EPUB narration compiler

Deployed M3/M4 implementation for the
[EPUB Narration Compiler project](../../docs/projects/EPUB-Narration-Compiler.md).
The repository contains no real book text, audio, timing or progress.

The modules establish these fail-closed contracts:

- `catalog.py` discovers Calibre EPUB rows through a SQLite read-only URI and
  rejects any source path outside the configured library root;
- `epub.py` extracts a bounded EPUB spine without executing content or allowing
  archive traversal;
- `state.py` persists the six-state generation lifecycle independently of
  Calibre; and
- `publication.py` validates an immutable manifest and atomically replaces a
  small ready pointer only after a complete generation is present;
- `monitor.py` performs idempotent new/changed-source reconciliation and emits
  only aggregate status; and
- `worker.py` claims one attempt under a file lock, validates the canonical
  voice contract, renders sentence units, verifies Opus/timing output and
  preserves the previous ready pointer on failure.
- `aster_books.py` is the inactive beta consumer contract. It loads only an
  atomic ready pointer, revalidates every generation member, pairs private
  normalized content with exact sentence cues, validates Ogg/Opus duration and
  keeps generation-bound progress in an owner-only atomic store.

`timing.py` records sentence cues as integer PCM sample indexes. It does not
invent word timing. `renderer.py` uses the pinned Kokoro model, voice and
cleanup hashes and verifies 48 kbit/s mono Opus duration before publication.
It retains a private hash-bound normalized chapter document for exact display
and highlighting; configuration backup excludes that source-derived content.

The deployed monitor is a daily persistent systemd timer in LXC 116. A separate
recurring timer invokes the single-attempt worker no sooner than five minutes
after the previous invocation becomes inactive. The worker also requires both
speech services to be active before it starts, retains its single-instance lock
and remains inside its low-priority resource envelope. Proxmox mounts the two
narrow NFS exports and bind-mounts the Calibre source read-only and the
AsterReader output read-write into the unprivileged guest.

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

Operational procedures and rollback are in
[the compiler runbook](../../docs/runbooks/EPUB-Narration-Compiler.md).

