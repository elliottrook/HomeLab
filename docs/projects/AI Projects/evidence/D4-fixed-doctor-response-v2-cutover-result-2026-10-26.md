# D4 fixed Doctor response v2 cutover result — 2026-10-26

## Result

**ROLLED BACK / NO-GO.** The approved caller-only cutover reached its bounded
canary, which returned `ok: false`. The script exited nonzero and automatically
restored the predecessor.

The independently queried predecessor then returned a valid schema-1
observation with source `homelab-doctor-structured/v2`, state `ok`, and age
13,622 seconds. This identified a contract mismatch: the source adapter accepts
observations through 36 hours, while the new presentation module accepted only
600 seconds. No answer text or private report content was retained.

## Recovery proof

- live caller SHA-256 restored to
  `aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a`;
- the new live response module is absent;
- the root-owned mode-0600 rollback copy has the predecessor hash;
- the fixed caller, fixed gateway, Aster Agent, accepted SYCL inference and
  Speech services are active;
- Aster Agent and accepted inference both retained restart count zero.

The caller was the only restarted service: once for the attempted cutover and
once for automatic rollback. No route, authority, model setting, credential,
OpenBao state or other production service changed.

## Correction

The response validator now imports the source adapter's `MAX_AGE` contract and
tests the observed failure range plus the exact 36-hour boundary. A corrected
inactive candidate and a new hash-pinned caller-only cutover are required
before any second live attempt.

