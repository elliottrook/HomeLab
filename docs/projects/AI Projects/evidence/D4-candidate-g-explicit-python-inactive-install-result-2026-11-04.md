# D4 candidate-g explicit-Python inactive install result — 2026-11-04

## Decision

**PASS — installed inactive and production-validated.** This closes the
deterministic exit-126 execution defect exposed by spent attempt r6. It does not
recover or score r6.

The source/installer is mirrored at platform commit
`0508488afe7d85155bfd518f2e05c76dce55172f`. Two deterministic builds matched
bundle SHA-256
`bd690ea920d2448f33b128394924a64b7f54e1082f648a55f8d3851954052c1f`.

## Installed identities

| File | SHA-256 | Custody |
|---|---|---|
| Host adapter | `e8c8cbcc875fe3f48035425f776a59f5ab81a6564f3f6acba38eb1dd63597a1b` | root:root 0644, one regular link |
| Release manifest | `7bbfd20888675768d544420e2d0a4f06e5c291f5c243c2e5dec3b2aa5d5596f0` | root:root 0644, one regular link |

The exact predecessors are root-only beneath
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-explicit-python-r1-20261104`.

## Acceptance

The installed 34-pin manifest loads. The fixed command is exactly rooted at
`pct exec 110 -- /usr/bin/python3 -B` followed by the registered wrapper path.
Direct target execution proves the explicit interpreter can read the
root-owned mode-0644 wrapper without changing its custody or starting the
listener.

The lease is ready; Doctor is healthy with zero codes; shared state/locks and
port-11436 listener are absent. Dispatcher, Doctor, EPUB, Proxmox daemons,
LXC104/110/116, Aster Agent, accepted 9B/SYCL llama and Speech are healthy,
with zero core restarts. No booking, model call, guest file change, service stop
or restart occurred during installation.

## Next gate

One new candidate-g transaction is now eligible only after an authoritative
full-window ledger check and fresh preflight. R3–R6 remain spent. A complete
result still requires 20 cases, exactly 14 requests, zero errors/retries/effects,
production restoration and later identity-blind review before any quality
decision.
