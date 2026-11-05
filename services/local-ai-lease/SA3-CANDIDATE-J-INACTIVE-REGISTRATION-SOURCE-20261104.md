# SA3 candidate-j inactive registration source — 2026-11-04

Candidate-j is registered as a distinct, fixed Lab Hours workload without
admitting a runner, installing a file or creating a booking. The registration
binds exactly five runtime files from Stream A commit `a13deb6d`: the six-case
public fixture, registered-hypothesis contract, selection-only runner, strict
public scorer and exact batch. Their source freeze is
`34b3fc5c2af1f51f50dddeed75397b37913a676803338880a12753e055169eea`.

The workload contains six cases but permits exactly two model requests; four
fail-closed cases never reach transport. It has zero retries, a 1,800-second
hard deadline, a 2,700-second minimum booking including a 900-second recovery
reserve, and a 262,144-byte result ceiling. Review material, answer keys,
candidate-g/i case-level judgments and arbitrary commands are excluded. A
pre-install dependency review found and removed the contract's stale import of
a candidate-i-era helper; the self-contained contract is now pinned at
`b243d429…b2af` and the corrected five-file freeze is
`34b3fc5c…9eea`.

The runner kind `sa3-evidence-matrix-candidate-j-public` is deliberately not
admitted by the reserved runner. This registration therefore cannot execute
the workload. No model call, booking, stop, restart, route, authority,
promotion or production effect is created. The next milestone is the fixed
candidate-j guest wrapper, host adapter and retained-result transaction with
independent source tests before any inactive installation.

Release manifest `sa3-candidate-j-registration-source-v12` pins the changed
registry along with the unchanged 35-file platform baseline. It is a source
integrity record, not an installation or activation instruction.
