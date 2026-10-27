# F2 Proxmox sbin path correction — inactive installation result

Status: **PASS — INSTALLED INACTIVE; NO SCAN OR TIMER EFFECT**

Jason approved the exact three-file replacement frozen by card `07cedd0a`.

The first installation attempt replaced the three files but its target test
command passed `.py` filenames to `unittest` as module names. All eight loader
entries failed before executing tests, and the rollback trap restored all
three exact predecessors. The corrected packet used module names and a new
rollback directory; no source candidate changed between attempts.

## Installed result

| Installed path | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `ce2332a1136b0176bd576a1c5c7f8f4a5374c45ef6d470dcbf78ffd594d4157f` | `root:root 0644`, one link |
| `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py` | `e072e90770c145c1a5f9cc3d589eb0d70d91230290cd70f0f82820efe5e109d0` | `root:root 0644`, one link |
| `/usr/local/libexec/local-ai-lease/f2_daytime_no_scan_rehearsal.py` | `20f3526735788cd25326c014ab855be1610be46164565c98243f195d1e94ff32` | `root:root 0644`, one link |

The successful target packet passed 60/60 tests. The installed rehearsal then
passed twice with identical bounded identities for the current VMID 104, 110
and 116 archives. Both results explicitly recorded
`archive_scan=not-attempted` and `receipt_written=false`.

Postchecks found no rehearsal or `zstd` child and no lease, lock or retained
receipt. Recurring F2 timers remain disabled/inactive; October 28 exact-date
units are absent. LXC104/110/116 are running and `pvescheduler`/`pvestatd` are
active. The predecessor files are retained at
`/root/aster-f2-proxmox-path-rollback-18c7198e-b/`.

This result proves the inactive installed correction. It does not constitute
an archive integrity result, F2/F3 evidence or approval for a timer, receipt,
lease, service stop, restart or model call.
