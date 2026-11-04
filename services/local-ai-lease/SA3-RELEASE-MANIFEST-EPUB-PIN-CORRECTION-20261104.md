# SA3 release-manifest EPUB pin correction — 2026-11-04

Status: **source complete; inactive installation pending**

## Exact failure and cause

Fresh booking `aster-stream-a-sa3-envelope-20261104-0930` was claimed exactly
at its scheduled start and failed closed before drain or model work:

- phase: `claim`
- code: `INSTALLED_PIN_DRIFT:full_inference_lab_sources.py`
- production restored: true
- elapsed: zero seconds

The approved two-file EPUB correction changed the installed source and
validator hashes, but `lab_hours_release_manifest.json` still pinned their
predecessors. Static preflight compared the installed files to the correction
card but did not exercise `lab_hours_reserved_runner.load_manifest()`, so this
internal release-manifest mismatch escaped until the authoritative claim.

## Correction

The manifest changes only the two EPUB-correction pins and its release label.
Its candidate digest is `4d8e7db2…2b92`; installed predecessor digest is
`c970bd70…9886`. The one-file inactive installer requires a ready lease and
absent shared state/locks, checkpoints the predecessor under root-only custody,
installs atomically, calls the actual installed `load_manifest()` to validate
every pin, and rolls back on any uncertainty.

No retry, reservation, service restart, workload, model call, routing or model
change is included. The failed booking remains terminal.
