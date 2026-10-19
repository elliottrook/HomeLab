# F2 fixed preflight wrapper — disabled-stage card

Status: source-only candidate; not installed, scheduled, or run. This card
does not authorize a scan, receipt, lease, timer, service change, or remote
push.

`scripts/local-ai/f2_preflight_fixed_wrapper.py` owns the cycle from the host
clock, the exclusion token from the fixed host path, the snapshot path, and
the complete installed dependency pin map. Callers cannot choose those values.
It runs the slow backup/TrueNAS/artifact/mirror/job preflight before the
01:10–01:19 boundary, atomically writes the root-custodied snapshot, and then
the fixed final guard re-reads current clock, lease readiness, exclusion,
absence, load, process quietness and every configured pin.

At 01:10 it requires only the 01:00 TrueNAS task to be complete after the
Proxmox artifacts; the 02:00 and 03:00 tasks are schedule-identity checks for
this window and are not incorrectly required to have run.

The snapshot records archive identity/metadata binding, not full archive
content integrity. F2/F3 retained-integrity and receipt gates remain separate.
Target staging must run the root-custody positive tests on Linux and verify
the exact installed paths, owner/mode, and rollback checkpoint before any
fresh-cycle approval is considered.
