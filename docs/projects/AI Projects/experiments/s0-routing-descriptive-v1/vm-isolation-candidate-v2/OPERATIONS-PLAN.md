# V3b corrected invented-fixture candidate

Status: **local source only; not staged or executed**

V3 failed before Python with systemd `226/NAMESPACE`. Approved forensics proved
that `InaccessiblePaths=/var/tmp/aster-s0-isolation-fixture-001` named a path absent
from the service's private temporary namespace. This candidate makes one boundary
correction: retain `PrivateTmp=yes` and move the planted non-secret read-denial
target to `/srv/aster-s0-isolation-fixture-002/canary`.

Everything material remains bounded: a fresh image import and new run/instance
identity; no vNIC, agent, credentials, package fetch, accepted corpus or tool call;
the same ten semantic checks; the same network/fork syscall denial, strict system
protection, 64-MiB/no-swap, one-task, 10%-CPU, 8-KiB-file and 15-second limits; and
the same digest-bound serial protocol and fail-closed validator.

The changed path fixes only the proven namespace collision. It does not assert that
the remaining controls work. V3b exists to test them. One complete result with all
ten checks true is required; any false/missing/extra check, malformed frame,
service setup failure, unbounded output, unexpected device or forced stop is a
failure. A pass would permit a new V4 boundary decision, not corpus execution.

Execution must use fresh VM121 and ISO/run identity `isolation-fixture-002`; it must
not reuse VM120's disk or boot any prior fixture. Creation stops for exact config
validation before a separately approved single boot. No retry or cleanup belongs
to the release.

