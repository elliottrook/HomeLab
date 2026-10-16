# Common host exclusion — corrected two-root disabled installation

**Observed October 16, 2026, 16:53–16:57 Vancouver.** Jason explicitly
approved the corrected seven-path disabled installation. This is a staging
result, not an archive integrity receipt, live lease, drill, F2/F3/F6 pass or
permission to enable an effect.

## Preflight and installation

- Proxmox state root was `root:root` 0700. Whole-host and A1 module roots were
  `root:root` 0755. The four replacements had the exact old hashes in the
  [V2 card](COMMON-HOST-EXCLUSION-DISABLED-INSTALL-CARD-V2-20261016.md);
  the three add-only paths and both lease state/lock pairs were absent.
- The A1 dependency had SHA-256
  `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d`.
  The source archive contained the six expected regular members; all source
  hashes matched the card. The host backup schedule digest was
  `ba63cd4f34e305fef29952f388799a0b0641806644105dde43a33fb73b36f622`.
  Both candidate timers were disabled/inactive and LXC104/110/116 active.
- Two installer invocations stopped at the A1 dependency check **before any
  installed-file change**. The prepared installer literal was truncated to
  57 hex characters; the reviewed card and live dependency both had the full
  64-character hash. We corrected only that literal, parsed all 11 installer
  hash literals to confirm 64 characters, and matched the replacement script
  SHA-256 on both sides:
  `b7535783064c921c295eb9fe59896f9a39f80783ba683feb9330563223909c23`.
- The corrected installer succeeded under the state-directory advisory lock.
  It saved four original files and a manifest in root-only checkpoint
  `/var/lib/local-ai-lab/host-exclusion-v2-checkpoint.ctixvq3t` (0700;
  files 0600). The seven installed paths are root-owned regular files mode
  0644 with the exact new hashes in the V2 card. The two `host_exclusion.py`
  copies both hash to
  `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563`.
  Each checkpoint original rehashed to its pinned old digest.

## Target-Linux checks and limits

- Five whole-host modules imported with the whole-host `PYTHONPATH` and the
  A1 controller plus its existing dependency imported with the A1
  `PYTHONPATH`, with bytecode writing disabled.
- A real second process using the A1 copy could not obtain a disposable
  state-directory lock held by the whole-host copy. Symlink and mode-0755
  custody were rejected. Both roots excluded each other while the actual
  state-directory advisory lock was briefly held, then released; no lock file
  or lease was created.
- The first 52-test synthetic Linux suite run had six fixture/environment
  failures: five A1 tests used `/tmp` (mode 1777) as the parent of an
  application lease directory, which the new host-root custody check
  correctly rejects; one test reads a repository-only watchdog unit file
  absent on the host. Re-running with a root-owned private test `TMPDIR`
  passed **51/51** behavioral fake-runner tests. The repository-unit-file
  source test was intentionally excluded from this host run; its source was
  not staged as a production unit. The full local source suite had passed
  earlier, but this target result does not claim the excluded test ran here.
- Installed producer and full-stop CLI `EFFECTS_ENABLED` flags were both
  `False`. Candidate watchdog and heartbeat services/timers remained
  disabled/inactive. No lease state or lock, archive receipt, archive scan,
  model call or service stop appeared. LXC104/110/116 remained active; both
  LXC114 News timers were enabled/active. The old manual lease executable and
  recovery executor retained their preflight hashes. The Proxmox backup
  schedule digest remained identical.

**Decision:** bounded disabled installation **PASS**. Preserve the checkpoint
and staged test material for rollback/provenance. F2/F3/F6 and the full-stop/A1
live gates remain **NO-GO** until their own separately approved and measured
work is complete. The old manual lease route still bypasses the common lock.
