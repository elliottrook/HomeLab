# SA3 candidate-j inactive registration source — 2026-11-04

Candidate-j is registered as a distinct, fixed Lab Hours workload without
admitting a runner, installing a file or creating a booking. The registration
binds exactly five runtime files from Stream A commit `a13deb6d`: the six-case
public fixture, registered-hypothesis contract, selection-only runner, strict
public scorer and exact batch. Their source freeze is
`7ab3bf93a326fad5748e5fe6f584d0b1a1bc890e78823059a19941832c0d3e74`.

The workload contains six cases but permits exactly two model requests; four
fail-closed cases never reach transport. It has zero retries, a 1,800-second
hard deadline, a 2,700-second minimum booking including a 900-second recovery
reserve, and a 262,144-byte result ceiling. Review material, answer keys,
candidate-g/i case-level judgments and arbitrary commands are excluded.

The runner kind `sa3-evidence-matrix-candidate-j-public` is deliberately not
admitted by the reserved runner. This registration therefore cannot execute
the workload. No model call, booking, stop, restart, route, authority,
promotion or production effect is created. The next milestone is the fixed
candidate-j guest wrapper, host adapter and retained-result transaction with
independent source tests before any inactive installation.

Release manifest `sa3-candidate-j-registration-source-v12` pins the changed
registry along with the unchanged 35-file platform baseline. It is a source
integrity record, not an installation or activation instruction.
