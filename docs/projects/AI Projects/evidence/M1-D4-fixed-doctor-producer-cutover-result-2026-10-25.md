# M1/D4 fixed Doctor producer — cutover result

**Date:** 2026-10-25  
**Source card:** Stream A commit `813798d7`  
**Decision:** producer cutover passed; fixed check remains fail-closed pending one corrected Doctor dependency

## Applied change

Jason approved the exact two-file cutover and builder-only canary. The live Mac
files now match:

- `build-aster-health-report.py` — `8ec44150b11e362896ad9662fed9cb0b26798c28a56ec6d447208d5cf67e23d7`;
- `scheduled-report.sh` — `76611cdef24340ec13dd8275c7237cb8d8f8b61d38a97a6ed09afebb500b544e`.

The unchanged LaunchAgent remained idle and scheduled at 08:15. Exact local
and LXC104 checkpoints are retained at:

- `/Users/jelliott/lab/private-backups/aster-stream-a/fixed-doctor-producer-pre-20261026T000132Z`;
- `/root/aster-fixed-doctor-producer-pre-20261026T000132Z` in LXC104.

## Canary result

The builder invoked Doctor once, published the schema-1/schema-2 pair and
finished inside the bound. Local and remote timestamps and aggregate digests
match. Local artifacts are mode `0600`; remote artifacts are root:`aster` mode
`0640`; both remote `.new` paths are absent. Aster and the normal broker stayed
active, both fixed-Doctor services stayed disabled/inactive and both sockets
stayed absent. The LaunchAgent was not run. F2/F6 and B60 were unchanged.

Doctor returned exit `1` with aggregate state `failed` because the existing
health run reported two unrelated operational failures. That health state did
not make the producer fail. The schema-2 fixed check safely returned
`unavailable`.

## Dependency found

The canary proved that the production Mac `doctor.sh` is still at SHA-256
`1f7f03d1033c0696d440e1d45d3e38f3691d7446a7596c120785275cd525e587`.
It predates the private-FD structured emitter and still describes the B60 path
as Vulkan. The producer therefore received no typed event and correctly
abstained. Replacing the entire Stream A Doctor would also import unrelated
changes, so that is rejected.

A narrow generator now applies only two changes to that exact predecessor:

1. add the private-FD/run-ID validated one-check emitter; and
2. replace only `check_aster` with the current accepted service/`xe` contract,
   removing the obsolete Vulkan probe and wording.

The generated one-file candidate is SHA-256
`c3f4d961fe7ce2b25990c0e1317a326eeefd82a80bfc6a6e2d74461fcdfe8e09`.
It passes `bash -n`; its patch-generator suite passes 3/3 and the complete
producer/capability boundary suite passes 40/40. Installing it and repeating
one builder-only canary are a separate change gate.
