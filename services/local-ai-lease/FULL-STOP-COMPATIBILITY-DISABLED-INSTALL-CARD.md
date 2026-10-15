# Disabled installation card: full-stop compatibility

Status: prepared, **not authorized or executed**. Source commit:
`f067dd05` on `codex/aster-lease-compat`; source pins are in
`FULL-STOP-COMPATIBILITY-SOURCE-PACKET.md`.

## Why and scope

Install the tested source as an **inactive candidate** on Proxmox so its
Python imports, file custody and controller/watchdog schema can be checked on
target Linux. This step does **not** run an archive scan, issue a lease, stop a
service, enable a timer, alter a backup schedule or call a model. The old
`/usr/local/sbin/local-ai-lease` remains byte-identical and is not used as a
full-stop acquisition controller.

Target: Proxmox only. Destination for Python modules:
`/usr/local/libexec/local-ai-lease/`. The new
`local-ai-lease-owner-heartbeat.{service,timer}` units may be copied to
`/etc/systemd/system/` but must remain disabled/inactive. No other unit is
enabled or started. No LXC, TrueNAS, Mac app, network, secret or key is changed.

Replace only these existing Python modules with their pinned candidate bytes:
`fixed_source_adapters.py`, `lease_contract.py`,
`lease_controller_candidate.py`, `platform_receipt_producer.py`,
`quiescence_receipt_adapter.py`, `source_receipt_boundary.py`, and
`trusted_observer.py`. Add only `full_stop_acquire_candidate.py`,
`full_stop_source_preflight.py`, `lease_owner_heartbeat.py`,
`retained_archive_integrity.py`, and
`retained_archive_producer_candidate.py`. Keep the installed
`lease_recovery_executor.py`, watchdog timer, admission schema and all other
files unchanged for this disabled stage.

## Preconditions and capture

1. Recheck the source commit and every SHA-256 against the source packet.
   Confirm branch has no unreviewed edits.
2. On Proxmox, confirm `/var/lib/local-ai-lab` is root-owned mode 0700,
   `lease.json` and `lease.lock` are both absent, and the watchdog and
   heartbeat timers are disabled/inactive. If any fact differs, stop.
3. Record SHA-256 and ownership/mode of each existing destination, the old
   controller, `lease_recovery_executor.py`, and watchdog units. Save the
   seven replaced module bytes in a root-only, mode-0700 checkpoint directory
   before replacing any file. Do not include credentials or private keys.
4. Check all five add-only module paths and two unit paths are absent. A
   conflicting path is a stop condition, not permission to overwrite it.

## Bounded installation and proof

Copy only the twelve named Python files and two disabled unit files. Require
root ownership and mode 0644 for code/units; retain the 0700 state directory.
Recompute every destination SHA-256 against the source packet. Run target-Linux
imports and the synthetic schema/receipt tests without invoking either CLI's
effect path. `full_stop_acquire_candidate.main(["--effect-authorized"])` and
the archive producer `main()` must still report disabled with no host effect.
Verify the old controller and installed recovery executor/watcher hashes did
not move; `systemctl daemon-reload` may load unit metadata but may not enable
or start units. Confirm neither new timer nor watchdog is running, no lease
file/lock appeared, and all production services and backup/News schedules
match the precheck. A separate approval is required for any actual archive
scan or full-stop drill.

The source packet's 173-test macOS result is not target-Linux validation.
The installed end-to-end path remains NO-GO until these target checks pass and
the next-cycle retained receipt, fixed runtime and watchdog are independently
verified. A1 and full-stop remain mutually exclusive per backup cycle.

## Rollback and abort

If any hash, import, state, service or schedule check fails, do not continue
to a live test. While **both** `lease.json` and `lease.lock` remain absent,
restore the seven replaced modules from the root-only checkpoint, remove only
the five newly added modules and two newly added units, reload systemd, and
recheck original hashes plus inactive timer states. Preserve the checkpoint
and failure evidence. If a state or lock unexpectedly appears, **do not**
swap controller/recovery code beneath it; retain the state and stop for
operator reconciliation.

This card is a concrete review target, not a standing approval or an instruction
to run the full-stop drill automatically at 03:10.
