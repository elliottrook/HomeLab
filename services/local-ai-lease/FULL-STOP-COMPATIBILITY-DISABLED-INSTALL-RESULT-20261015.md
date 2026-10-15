# Full-stop compatibility: disabled host installation result

**Observed 2026-10-15, 15:19 America/Vancouver.** Jason approved the exact
disabled installation in this conversation. Source branch
`codex/aster-lease-compat` at `d96bf2a2`; the fourteen source files matched
every SHA-256 in `FULL-STOP-COMPATIBILITY-SOURCE-PACKET.md` before transfer and
again in root-only staging. No live-drill approval was given or used.

The Proxmox precheck found root-owned mode-0700 `/var/lib/local-ai-lab`, no
`lease.json` or `lease.lock`, disabled/inactive watchdog and absent heartbeat
units. The seven existing modules were root-owned mode 0644. Their original
bytes were preserved at
`/var/lib/local-ai-lab/checkpoints/full-stop-compat-20261015-d96bf2a2/`
under a mode-0700 directory, before replacement. Its `stage/` child contains
the exact transferred candidate. The five add-only module destinations and
two heartbeat unit paths were absent before installation.

Installed only the twelve pinned Python modules in
`/usr/local/libexec/local-ai-lease/` and the two pinned heartbeat units in
`/etc/systemd/system/`; code and units are root-owned mode 0644. Reloaded
systemd metadata without enabling or starting a unit. Destination bytes
matched staging with `cmp`, and `systemd-analyze verify` passed. The old
`/usr/local/sbin/local-ai-lease`, recovery executor and watchdog timer retained
their recorded SHA-256 values `f9744b4e…`, `d75ddfae…`, and `9f09de46…`.

Target Proxmox Python 3.13.5 imported the installed candidate and recovery
modules with `PYTHONPATH=/usr/local/libexec/local-ai-lease` and `-B`. A
synthetic `AdmissionRecord` encoded/decoded identically; the installed
archive `capture` exposes `deadline_epoch`. Both candidate effect flags were
false, and calling their CLI entry points returned `disabled` with
`effects: not-attempted`. A synthetic fixed-source retained-backup exercise
passed against the **installed older** `source_receipts.py` and
`backup_receipt_adapter.py`; it made no archive scan or remote query.
The installed-path full-stop acquisition suite ran **7/7** target-Linux tests.
The controller suite ran **16/16 applicable** target-Linux tests; its one
repository-relative unit-file assertion was skipped because the tests were
streamed over stdin, so `__file__` cannot locate the repository tree. The
installed unit files were independently checked with `systemd-analyze verify`
and pinned-byte comparison. An initial unmodified stdin run reported that
single `__file__` harness error; it was not a controller failure.
Additional installed-path target-Linux suites passed: watchdog **10/10**,
trusted observer **8/8**, retained archive producer **6/6**, and retained
archive integrity **6/6**. Recovery executor tests passed **3/3 applicable**;
the repository-relative unit-path assertion was skipped over stdin and the
installed watchdog unit was inspected directly. It has
`RefuseManualStart=yes`; its timer is periodic but disabled/inactive. These
are synthetic tests and unit inspection, not a powered recovery drill.

Postcheck: no lease or lock; both heartbeat and watchdog timers still
disabled/inactive; LXC104, 110 and 116 running; `pvescheduler` active; News
digest timer active/enabled in LXC114. No production consumer, backup schedule,
model, credential, firewall, OpenBao or Companion setting was changed.

**Still NO-GO for a live full-stop or A1 benchmark.** The install proves
installed-path compatibility, not a fresh current-cycle retained archive
receipt, enabled independent watchdog, bounded recovery drill or exact
post-recovery SYCL/schedule restoration. The candidate CLIs are deliberately
hard-disabled. A separately reviewed and approved live path must satisfy
those gates; do not treat this result as authorization to enable effects.

Rollback, if needed while both lease state and lock remain absent: restore
only the seven original modules from the checkpoint, remove only the five
new modules and two new heartbeat units, run `systemctl daemon-reload`, and
verify original hashes and inactive timers. If state or lock appears, stop
instead of changing code beneath a possible lease.
