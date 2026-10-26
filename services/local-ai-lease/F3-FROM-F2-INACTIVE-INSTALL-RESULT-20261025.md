# F3 retained receipt from F2 — inactive installation result

Status: **PASS — INACTIVE SOURCE COMPATIBILITY ONLY**

Jason approved the exact single-file inactive installation on 2026-10-25.
The installed source is commit `de23781c`; its independent source review was
GO. This transaction did not invoke the converter or authorize an F3 receipt.

## Installed identity

| Target | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f3_from_f2_result.py` | `64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421` | `root:root 0644`, regular, one link |

The target was absent before installation. Its three installed dependencies
matched the hashes in the inactive-install card before the transaction.

## Validation

- The installed-path import passed with bytecode writing disabled.
- The converter, retained-integrity and F2 coordinator suites passed 27/27 on
  target Linux.
- The first target test invocation omitted existing F2 dependency modules from
  its temporary fixture and stopped at test collection. Supplying the installed
  dependency directory to that temporary fixture produced the complete 27/27
  pass. This was a fixture packaging error, not an installed-source failure.
- `/var/lib/local-ai-lab/archive-integrity.json` and the October 26 F2 cycle
  state remained absent.
- The exact October 26 F2 preparation and final timers remained enabled and
  active for 01:15 and 01:20 PDT respectively.
- The lease remained `ready`; no F2/F3 process or `zstd -t` child was present.

This result does not create F3 evidence, scan an archive, acquire a lease,
stop a service, call a model or advance F4/F5/F6. If F2 produces exactly three
independently reconciled exit-zero rows, the next serial gate is a separate
approval to invoke the converter once. A failed or uncertain F2 result writes
nothing.
