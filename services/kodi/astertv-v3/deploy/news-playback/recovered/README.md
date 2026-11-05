# Recovered News playback predecessors

These are the exact pre-repair inputs saved by the accepted Family and Jen
checkpoints. Their hashes match `repair.py::BASELINES`. The fleet materializer
replays the current `build_payload` from these inputs and verifies the three
installable outputs against pinned renderer results. Jen already has this
revision; Family's accepted marker is the earlier revision, so its candidate is
deliberately advanced to the same bounded-queue implementation rather than
freezing the older live bytes.

The per-host `family-manifest.json` files are renderer inputs only. They prove
that each wrapper/component pin was valid before transformation, but the shared
manifest is not installed by this overlay because other overlays also update
it. Runtime verification asserts that its digest-player component matches the
installed manifest instead.
