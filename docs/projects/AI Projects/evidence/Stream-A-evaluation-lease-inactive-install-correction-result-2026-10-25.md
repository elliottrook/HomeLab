# Stream A evaluation-lease inactive-install correction result — 2026-10-25

> Result: **PASS — INERT FOUR-FILE CANDIDATE COMPLETE**

Jason approved the bounded correction in
`Stream-A-evaluation-lease-inactive-install-correction-card-2026-10-25.md`.
The retained Proxmox directory contained exactly the four pinned source files
and the two previously observed generated `.pyc` files beneath `__pycache__`.
All source hashes matched platform manifest SHA-256
`f14f2e8860c0e783fd9777374393e46b02123ff15125e78f5e43594ea670e83d`.

Only the generated cache files and empty cache directory were removed. AST
parsing and imports passed with bytecode writes disabled. The watchdog returned
the semantic state `effects=disabled`, `state=source-only`; its ordinary JSON
spacing differed from the first shell check's compact string, so the check was
repeated semantically without changing source bytes. The final directory is
root-owned mode `0755` and contains exactly four root-owned mode `0644` files
with the pinned hashes. No bytecode, unit, timer, entry point, lease, operation
lock or runtime state exists.

This completes only the inactive library installation. It does not enable an
effect adapter, acquire a lease, stop a consumer, call a model, alter F2 or
authorize an evaluation workload.
