# Recovered TV-details outputs

These four files are the canonical final outputs of the exact-hash TV-details
upgrade chain applied on 2026-11-02. They are not an unqualified snapshot of
mutable appliance state.

The predecessor hashes for every transition remain recorded in the bounded
transformers beside this directory and in `lineage.json`. Bedroom checkpoints
were read back on 2026-11-05 and matched every declared predecessor from the
v2.0.7 baseline through the cache-limit finish. Family independently matched
the final hashes byte-for-byte.

The materializer verifies these bytes and every renderer hash before emitting
an install tree. The shared `family-manifest.json` is deliberately excluded:
it is composition state and differs per appliance as other overlays are
applied. Its TV-details component pin is instead a typed runtime assertion.
