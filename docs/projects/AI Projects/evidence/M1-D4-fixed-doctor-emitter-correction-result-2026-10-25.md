# M1/D4 fixed Doctor emitter correction — live result

**Date:** 2026-10-25
**Source:** Stream A commit `cb7de612`
**Decision:** PASS; same-run fixed state is now typed and digest-bound

Jason approved the exact one-file correction and one builder-only re-canary.
The live Mac Doctor now matches SHA-256
`c3f4d961fe7ce2b25990c0e1317a326eeefd82a80bfc6a6e2d74461fcdfe8e09`
as `jelliott:staff` mode `0755`. Its predecessor is retained at
`/Users/jelliott/lab/private-backups/aster-stream-a/fixed-doctor-emitter-pre-20261025T1715PDT`.
The matching LXC104 report checkpoint is
`/root/aster-fixed-doctor-emitter-pre-20261025T1715PDT`.

The single re-canary completed inside the bound. The fixed
`aster.agent_inference` state is `pass`. Its local and LXC104 schema-1 digest,
timestamp and schema-2 state match exactly; both remote `.new` paths are
absent. Local report artifacts are mode `0600`, and remote reports remain
root:`aster` mode `0640`.

The overall Doctor exit remains `1` and aggregate state remains `failed`
because two unrelated operational checks are failing. That broader health
state is retained independently and did not alter the fixed inference result.
No free text entered schema 2.

Aster Agent and the normal broker stayed active. Both fixed-Doctor services
remain disabled/inactive, both sockets remain absent, and the 08:15 LaunchAgent
stayed idle and unchanged. No broker replacement/restart, enrollment, grant,
fixed read, model call, schedule change or F2/F6/B60 action occurred.

The producer/evidence gate is complete. The initially pinned broker candidate
was subsequently rejected because it predates live Forgejo project-document
support. The superseding exact-live-source reconciliation preserves that route;
its separately reviewed two-file replacement and one controlled normal-broker
restart are the next bounded gate, still without enrollment or service
activation.
