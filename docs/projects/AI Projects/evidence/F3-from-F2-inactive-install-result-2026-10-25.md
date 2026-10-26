# F3-from-F2 converter inactive installation

**Date:** 2026-10-25
**Decision:** inactive installation **PASS**; receipt production remains **NO-GO**

Jason approved installation of the single source-reviewed converter from
platform commit `de23781c`. Proxmox now has
`/usr/local/libexec/local-ai-lease/f3_from_f2_result.py` as a root-owned,
mode-`0644`, regular one-link file with SHA-256
`64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421`.
The target was absent beforehand and all three installed dependency hashes
matched the frozen card.

The installed module imported successfully with bytecode disabled. Its
converter, retained-integrity and F2 coordinator suites passed 27/27 on target
Linux. The first invocation omitted existing F2 dependency modules from its
temporary fixture and stopped during collection; adding the installed module
directory to that fixture produced the complete pass. No converter effect ran.

Postchecks found the October 26 F2 cycle state and retained receipt absent,
both exact-date F2 timers unchanged and active for 01:15/01:20 PDT, the lease
`ready`, and no converter, scanner or `zstd -t` child.

The converter is inert. It may be invoked once only after independent
reconciliation of a complete F2 result with exactly three exit-zero archive
rows and a separate effect approval. It performs no second archive scan. A
failed, partial, stale, changed or uncertain F2 result cannot create a receipt.
