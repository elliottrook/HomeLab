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

The first `v1` installation stopped before checkpoint or target write because
the installer required repository source files to carry their eventual target
executable mode. The corrected `v2` installer verifies source identity and
custody independently, then applies the pinned target modes atomically under a
fresh checkpoint identity. The failed `v1` stage is retained and must not be
retried.

The corrected focused suite passes 53/53. Two independent `v2` bundle builds
match SHA-256 `5f4a50d4cbae3021775756b3754ec7226047775df9e5e02cccc106fb30b0fc12`.
