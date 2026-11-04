# D4 candidate-g release-manifest pin NO-GO — 2026-11-04

## Decision

**TIMED TEST: NO-GO; NO WORKLOAD OR SERVICE EFFECT; NO RETRY.**

Booking `aster-stream-a-sa3-envelope-20261104-0930` was atomically claimed at
09:30 host-local and failed in zero seconds:

- first failure phase: `claim`
- failure code: `INSTALLED_PIN_DRIFT:full_inference_lab_sources.py`
- production restored: true
- model requests: 0
- service stop/start: 0
- retry: 0

Independent postchecks found the lease ready, shared drain state/lock and
operation lock absent, no candidate-g process, dispatcher/Doctor and Proxmox
daemons active, LXC 104/110/116 running, Aster Agent/accepted llama/Speech
active, and EPUB still timer-inactive/worker-activating.

## Root cause

The installed two-file EPUB correction was exact, but the root-owned Lab Hours
release manifest still pinned both predecessor hashes. Static preflight checked
the changed files against the correction card rather than invoking the reserved
runner's complete installed-manifest verifier. The authoritative claim
therefore rejected the internally inconsistent release before any drain.

Platform source now updates only those two pins and adds a reversible one-file
inactive installer. The corrected manifest and installer/runner/workload suite
pass 22/22 locally. A later installation must execute the actual installed
`load_manifest()` call before another booking is considered. The spent booking
is terminal and must not be retried.
