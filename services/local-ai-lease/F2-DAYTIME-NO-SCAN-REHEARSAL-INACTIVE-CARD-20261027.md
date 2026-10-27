# F2 daytime no-scan rehearsal — inactive installation and run card

Status: **SOURCE TESTED; HOST CHANGE AND RUN NOT YET AUTHORIZED**

The October 20–27 attempts exposed one integration fault per overnight cycle.
Unit tests used process fakes or stopped above the installed child boundary,
while failure projection discarded the next useful phase. A fresh timer must
not be activated until the exact installed data and process path can be
rehearsed during the day without running an archive integrity scan.

## Frozen candidate

Source commit: `28edce6d628496023875e17a5680a7682b3262c0`

| Item | SHA-256 |
|---|---|
| `scripts/local-ai/f2_daytime_no_scan_rehearsal.py` | `352576c0d79064727642d13ef11f3e4d9e61936bbf223275b89cc1685d56c5f7` |
| `scripts/local-ai/test_f2_daytime_no_scan_rehearsal.py` | `8ad7be8bf648b594c2c5322488ee2fc703a143340adda02dc2eed83ca1354423` |

The candidate pins and imports the installed producer, integrity module,
fixed-source adapter and backup-receipt adapter. It launches a real Python
child with `Popen.communicate()`, then uses the existing producer to validate
the current cycle's fixed Proxmox job, three guest completions, whole-job
journal, TrueNAS task 1, exact archive inventory, resolved paths, identity,
size and deadline arithmetic. Only the probe injected below `capture()` is
replaced with `(exit=0, elapsed=0)` and the save callback is a no-op. It does
not open archive contents or invoke `zstd`.

The result schema says `archive_scan=not-attempted` and
`receipt_written=false`; it cannot be consumed as F2 or F3 evidence. The real
subprocess transport test and the existing F2 suites pass 57/57 locally.

## Bounded target action

After separate approval, the platform owner may:

1. require the four pinned dependencies at exact root-owned, one-link mode
   `0644` hashes;
2. install only the new rehearsal file at
   `/usr/local/libexec/local-ai-lease/f2_daytime_no_scan_rehearsal.py` as
   root-owned, one-link mode `0644`;
3. run the frozen test packet on target Linux;
4. invoke the rehearsal twice with `--no-scan-authorized`, using the current
   completed backup cycle; and
5. verify identical bounded three-archive results, no `zstd` or F2 child,
   no lease/lock/receipt, unchanged timers and healthy production.

Any source, custody, current-cycle or process-chain mismatch is a daytime
NO-GO. Diagnose and correct it before presenting another exact-date timer.
Rollback removes only the newly installed rehearsal file after verifying no
rehearsal child exists.

This card authorizes no host change or run by itself. It does not authorize an
archive scan, F2/F3 result, receipt, lease, service stop, restart, model call,
timer activation, schedule change or Git push.
