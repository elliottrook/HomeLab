# SA3 candidate-j deterministic inactive installer source — 2026-11-04

The candidate-j inactive installer is source-complete and not applied. It
accepts only a deterministic bundle binding Stream A commit `272d4e55` and the
current platform source. It replaces four exact installed host files, adds
three candidate-j host modules and adds the self-contained five-file runtime
plus wrapper to LXC110. It rejects baseline drift, existing targets, any
candidate-j unit, non-ready lease state or shared operation state/lock.

Before mutation it retains root-only host and guest checkpoints. Every source
and target is hash/custody checked; post-install proof imports the exact host
and guest paths, requires all 39 release pins, and proves the workload is
registered and runner-admitted while no unit or booking exists. Failure rolls
back only bytes that still match the intended candidate-j targets and fails
closed on uncertainty.

The CLI is a no-op without `--apply`. Bundle construction is deterministic and
contains 15 entries including its manifest. Focused tests cover the exact
change boundary, source hashes, no-op default and repeatable cross-commit
bundle. Applying this package remains a separate inactive installation effect;
it does not authorize a booking, model call, service stop/restart, route,
authority or promotion.
