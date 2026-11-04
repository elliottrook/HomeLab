# Aster Lab Hours SA3 envelope booking r7 card — 2026-11-04

## Booking

- ID: `aster-stream-a-sa3-envelope-20261104-1530-r7`
- Owner/workload: `aster-stream-a` / `sa3-evidence-envelope-quality-v1`
- Window: 15:30–17:00 America/Vancouver, including 900-second recovery buffer
- Authoritative ledger at 15:10: clear, no booking IDs

R7 is one fresh attempt. R3–R6 are spent. Its fixed purpose is the frozen
20-case/14-request candidate-g result or one bounded failure projection.

## Installed pins

- workload registry: `3bcfefd8942bbc8f31db70bce51a04ff17ce2f13adb352d816ae6cdd7237be73`;
- release manifest: `7bbfd20888675768d544420e2d0a4f06e5c291f5c243c2e5dec3b2aa5d5596f0`;
- host adapter: `e8c8cbcc875fe3f48035425f776a59f5ab81a6564f3f6acba38eb1dd63597a1b`;
- LXC110 wrapper: `626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`.

Installed proof validates all 34 pins, exact explicit-Python command shape,
target wrapper readability, ready lease, absent shared state/locks/listener,
healthy zero-code Doctor and production, and zero core restarts.

## Runtime and terminal boundary

The dispatcher must recheck the exact booking, pins, lease, operation lock,
listener absence, production health and restoration reserve at claim. Accept
success only for 20 cases, exactly 14 requests, zero errors/retries/effects,
frozen identities, retained digest, exit zero, `production_restored=true`, no
remaining candidate state/listener/lock, ready lease and healthy independent
postchecks.

Any other state is NO-GO without retry. Retain no prompt, answer, case identity,
traceback message or arbitrary output. No model/backend change, restart,
blind-review claim, route, tool grant or automatic promotion is authorized.
