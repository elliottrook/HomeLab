# Retained archive producer CLI: source-only checkpoint

**Status:** offline candidate; no host installation or live scan. The installed
producer remains at the earlier pinned bytes with `EFFECTS_ENABLED = False`.
This checkpoint does not close Stream A full-stop dependency F3.

The retained archive producer already verifies the fixed 00:30 Proxmox job,
all three guest completion logs, the completed 01:00 TrueNAS task, current-day
archive identities and bounded sequential `zstd -t` results before its
root-owned receipt writer runs. Its prior `main()` could only print
`disabled`, leaving no callable reviewed command path for a future F3 release.

This source candidate adds a command path behind **both** a source-level
`EFFECTS_ENABLED` flag and a one-shot `--effect-authorized` argument. The flag
remains **False**. Even in an isolated test where the flag is patched true,
the entry point refuses a non-root caller or an existing lease/lock before
calling `produce`. Its success output contains only date and archive count;
source command output, archive names and contents are not printed. The fixed
runner does not accept a user-supplied command.

Source SHA-256 after the change:

- `retained_archive_producer_candidate.py`:
  `dc74134e55db19d7c22c300968fcfcf1dfcca3aaaea0d33bf8616a2cb6346fb3`
- `test_retained_archive_producer_candidate.py`:
  `1e4fa1465047068a638760eff46fd39ad17142eba6f15cd2554d129ddf66d69e`

Focused offline suite: 20 tests passed across producer, retained integrity
and acquisition candidates. Tests substitute a temporary directory and mock
the actual scanner for the effect-entry checks. No model, Proxmox archive or
TrueNAS source was contacted.

Before F3 can be marked complete, a separate reviewed release must pin the
effect-enabled source bytes, test them on target Linux with fixed-source
failures and receipt custody, approve and install only the bounded producer,
confirm no lease/lock and backup contention, run it in an eligible fresh
backup cycle, and independently reread the receipt against unchanged archive
identities. The October 16 read-only timing scan cannot substitute for this.
The independent watchdog and live full-stop approval remain separate gates.
