# Run 003 evidence

Run 003 was invoked exactly once on 2026-09-26 under the fresh approval recorded
in `RUN-003-GO-NO-GO.md`. The launcher verified the reviewed manifest, approval
record and both prior evidence sets before creating its exclusive journal.

Preflight passed. The unit-state, path, guest-health, host-resource and DNS checks
completed, after which the owned one-byte canary was created. The transient unit
was then attempted but never produced its readiness record. The bounded failure
code is `run-readiness` / `validation`.

Read-only diagnosis found the exact transient invocation failed with
`status=226/NAMESPACE`, `Result=exit-code`, `MainPID=0`, no cgroup and no runtime
probe. This is evidence that the reviewed systemd isolation combination could not
be established inside LXC100; it is not an application-model or accepted-corpus
result. The payload did not reach its readiness output.

Manual recovery revalidated the exact invocation ID and every canary receipt
field, reset only that failed transient unit, then removed only the inode-matched
canary. Final checks prove the unit is `not-found`, canary/runtime/cgroup paths are
absent, systemd is `running`, and the Docker service baseline is restored. No
automatic stop or retry occurred.

This result triggers the run-003 hard stop. Do not perform a fourth shared-host
attempt by weakening namespace controls. Further work must change the execution
context or isolation method and begin with a new architecture/evidence decision.
