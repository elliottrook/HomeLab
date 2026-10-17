# F2 failure-phase candidate — source only

The approved October 17 read-only F2 attempt returned `F2NoGo` without archive
rows. The installed guard reports only an error class, so the record cannot
establish whether a preflight predicate, observer process, or result projection
failed. Later passing read-only predicates do not reconstruct the failed
instant.

This source-only candidate adds one fixed, content-free `phase` value to a
future guard failure: `preflight`, `observer`, or `result`. It does not expose
child output, archive paths, private data, or exceptions. It does not change
the fail-closed decision, scan limits, lease behavior, host effects, or the
October 17 result. A phase narrows a future investigation; it does not identify
which predicate failed or prove archive integrity.

The current checkout's `scripts/local-ai` suite passed 208 tests (four
root-custody tests skipped on macOS), including phase assertions for preflight
denial, observer failure, and malformed result. This candidate is **not
installed**. Its changed hash requires target-Linux review, a new pinned
release card, separate host change approval, and fresh one-cycle scan approval
before use. Never rerun the October 17 attempt to diagnose it.
