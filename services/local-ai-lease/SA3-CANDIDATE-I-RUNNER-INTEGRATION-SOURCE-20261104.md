# SA3 candidate-i reserved-runner integration source — 2026-11-04

Candidate-i's fixed runner kind is now admitted in source and joined to the
existing full-drain lifecycle. The reserved runner accepts only the registered
workload identity, exact 20-request receipt, 14 model requests, zero errors,
complete retained-result digest and `production_restored=true`. The full
runtime dispatches that profile only to the candidate-i transaction and
listener adapter.

The source change also adds candidate-i process detection to the quiet-host
gate and pins the two new host modules plus changed reserved-runner/runtime
files in release manifest `sa3-candidate-i-transaction-source-v11`. Joined
tests exercise both the runtime dispatch and full reservation-to-terminal
receipt path. The combined focused suite passes 53/53 after updating the exact
36-file manifest count.

This is source integration only. Installed production still lacks the changed
runner/runtime/manifest and all candidate-i guest files, so candidate-i cannot
run. No booking, model call, stop/restart, route, authority or promotion is
created. A deterministic inactive installer with rollback and exact target
proof is the next milestone.
