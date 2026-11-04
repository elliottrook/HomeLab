# Aster Lab Hours SA3 envelope booking r8 card — 2026-11-04

## Booking

- ID: `aster-stream-a-sa3-envelope-20261104-1615-r8`
- Owner/workload: `aster-stream-a` / `sa3-evidence-envelope-quality-v1`
- Window: 16:15–17:45 host-local offset `-07:00`, including the fixed
  900-second recovery reserve
- Authoritative ledger at 15:47: clear, no booking IDs

R8 is one fresh attempt. R3–R7 are spent. Its fixed purpose is the frozen
20-case/14-request candidate-g result or one bounded failure projection.

## Installed pins

- workload registry: `49fc9ebfb703437e4735093e5f0ed08a1d29ea2fa966b1cf0294b88c9d88a174`;
- release manifest: `8717c42c8bb24f33ee24cf176b11457766b88e5a90723142bad28842978d55a2`;
- host adapter: `e8c8cbcc875fe3f48035425f776a59f5ab81a6564f3f6acba38eb1dd63597a1b`;
- LXC110 runner: `372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352`;
- LXC110 wrapper: `1c0240fe7ad1c8f11b22410ecb8938edc6a056007f7f1e578ce0c484ec3c9697`.

Installed proof validates exact custody, all 34 pins, bounded known-metadata
normalization, unknown-key rejection, ready lease, absent shared
state/locks/listener, healthy zero-code Doctor and production, and zero core
restarts.

## Runtime and terminal boundary

The dispatcher must recheck this exact booking, pins, lease, shared lock,
listener absence, production health and restoration reserve at claim. Accept
success only for 20 cases, exactly 14 requests, zero errors/retries/effects,
frozen identities, retained digest, exit zero, `production_restored=true`, no
remaining candidate state/listener/lock, ready lease and healthy independent
postchecks.

Any other state is NO-GO without retry. Retain no prompt, answer, case identity,
response body, exception text or arbitrary output. No model/backend change,
restart, blind-review claim, route, tool grant or automatic promotion is
authorized.
