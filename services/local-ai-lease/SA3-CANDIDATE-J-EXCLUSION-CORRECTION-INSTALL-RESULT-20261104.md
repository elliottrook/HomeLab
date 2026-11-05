# SA3 candidate-j exclusion correction install result — PASS — 2026-11-04

The bounded correction installed inactive after the spent R1 failure. It
replaced only the candidate-j wrapper on the host and in LXC110 plus the host
release manifest. Root-only rollback checkpoint
`sa3-candidate-j-exclusion-r1-20261104` is retained.

Installed wrapper SHA-256 is `a883c144…5f2a` in both locations. The derived
41-pin manifest is `1f048141…c845`; it changes only that wrapper pin from the
installed `66164c8c…8b24` baseline and preserves EPUB alignment adapter
`59d47d79…af8c` and transaction `fb4cbcb5…a50`. The result reported two host
replacements, one guest replacement, no booking, no workload effect and no
service restart. Lease ready, absent shared state/locks and exact hashes passed
independent postcheck. The first attempt without the source-only helper failed
before mutation; the exact helper was then staged and the verified installer
completed.

R1 remains terminal and is not retried. The authoritative ledger showed the
22:15 AsterTV alignment booking and recovery window, so corrected R2 uses the
first complete clear window instead: 23:00–23:45.
