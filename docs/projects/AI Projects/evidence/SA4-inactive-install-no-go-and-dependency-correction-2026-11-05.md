# SA4 inactive-install NO-GO and dependency correction — 2026-11-05

## Measured result

Jason approved the exact 17-file inactive installation from Stream A commit
`1602ecb0`. A fresh no-follow preflight found all three parent paths absent.
LXC 104/110/116, Aster Agent, accepted llama/SYCL, Aster Speech,
`pvescheduler` and `pvestatd` were healthy. The staged bytes matched every
approved digest, and the exact files were installed root:root with the fixed
modes and one link.

The first isolated import postcheck failed before any checkpoint, grant,
repair or service effect:

- phase: `inactive-install-postcheck`
- class: `incomplete-source-dependency-closure`
- code: `missing-nlu-threshold-policy`
- measured error: `ModuleNotFoundError: nlu_threshold_policy`

Several fixed SA4 validators import the shared unique-JSON decoder from
`nlu_threshold_policy.py`, but the 17-file packet did not include that module.
This was a deterministic source-packet defect, not a host, model, service,
booking, lease or credential failure.

## Recovery

All installed hashes, owners, modes and link counts were unchanged. The exact
17 payloads were removed, followed by the three empty packet-owned
directories. A no-follow reread confirmed all three parent paths absent.
Production remained healthy: Aster Agent, accepted llama/SYCL, Aster Speech,
`pvescheduler` and `pvestatd` were active after rollback. No SA4 unit, process,
key, grant, checkpoint, receipt or repair effect existed.

## Correction

The corrected packet adds only the missing source dependency,
`nlu_threshold_policy.py`, pinned to SHA-256
`984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d`.
The payload is now exactly 18 files. A new isolated-environment test copies
only the declared libexec payloads and imports every declared module using
Python isolated mode with bytecode disabled. This proves the installed import
closure rather than inheriting repository paths accidentally.

The complete SA4 source suite passes **68/68**. Nothing is currently installed.

## Next gate

The corrected 18-file inactive installation is a different remote mutation
from the approved 17-file packet and therefore needs exact approval. It still
creates no key, grant, booking, checkpoint, repair, service unit, timer,
restart, model change or route. After installation, the same metadata/hash
checks plus the new isolated import check must all pass before SA4 advances.
