# SA3 reserved-runner activation — no-execution install card

Status: **source-complete; workload execution requires a later reservation**

This candidate connects the already installed transaction and listener adapter
to the fixed reserved runner. It replaces the full-drain runtime, reserved
runner and release manifest against their exact installed hashes. The runtime
admits only the registered SA3 profile, collects a 2,700-second preflight,
drains through the existing fixed controller, starts only the fixed LXC110
wrapper, retains the bounded result under the booking's root-only attempt
directory, proves listener/GPU absence, and restores production. The guardian
remains the owner-loss recovery authority.

Installation is blocked by any active SA3 reservation. It creates no booking,
timer, service, lease, model request, drain or restart. Actual execution still
requires the authoritative Lab Hours window check and reservation, then the
existing whole-host lease and shared operation lock gates.

The focused transaction, adapter, runtime, runner, reservation, registry and
installer suite passes 53/53. Two independent deterministic builds match
SHA-256 `be99bfbfaf34e3a9b741b23d081edd302cf5c8b942fa9b93299910135909aef2`.
