# F3 retained receipt from F2 — inactive install card

Status: **SOURCE REVIEW GO; INSTALLATION NOT YET AUTHORIZED**

This card stages one source-only converter before the October 26 F2 window. It
does not invoke it, write the retained receipt, scan an archive, change either
F2 timer, acquire a lease, stop a service, call a model or advance F4/F5/F6.

Independent review accepted source commit `de23781c` for this inactive design.
The combined F3, retained-integrity and F2 coordinator suite passed 27/27.

## Exact target

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/f3_from_f2_result.py` | `/usr/local/libexec/local-ai-lease/f3_from_f2_result.py` | `0644` | `64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421` |

The target is currently absent. Its required installed dependencies have been
read-only reconciled as root-owned regular mode-`0644`, one-link files:

| Installed dependency | SHA-256 |
|---|---|
| `backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |
| `f2_scheduled_release_candidate.py` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` |
| `retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |

## Inactive transaction

1. Require the target and `/var/lib/local-ai-lab/archive-integrity.json`
   absent. Recheck the three dependency hashes/custody and both October 26 F2
   timers enabled, active and waiting.
2. Copy only the pinned converter as `root:root 0644` and verify its hash,
   regular-file type and link count.
3. Import it with Python bytecode disabled. Run the converter, retained
   integrity and F2 coordinator tests from a complete temporary test fixture;
   require 27/27 passes.
4. Recheck the receipt and October 26 cycle state are absent, the two timers
   are unchanged, no F2/F3/zstd child exists, and no lease or lock appeared.

## Later effect boundary

After an independently reconciled, complete October 26 F2 result with exactly
three exit-zero rows, a separate approval may invoke exactly:

`/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/f3_from_f2_result.py`

The converter reads only the fixed current-date root-custodied F2 terminal
state, re-resolves and re-stats the same current archives, validates the
constructed receipt through the installed retained-integrity verifier,
rereads unchanged F2 bytes and atomically creates the fixed F3 receipt once.
It performs no archive scan. NO-GO, partial, stale, substituted, changed or
uncertain evidence writes nothing and cannot retry automatically.

## Rollback

Inactive rollback removes only the newly installed converter after verifying
its exact hash and rechecks the absent receipt/state effects and unchanged F2
timers. A later uncertain receipt write is never deleted under this rollback;
it is retained for reconciliation.
