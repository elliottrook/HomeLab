# F2 diagnostic guard — disabled host replacement result

**Decision:** disabled replacement PASS; F2 timing remains NO-GO and was not
run. The approved change targeted the Proxmox host root, where the guard is
installed; it was not an LXC file. No `--read-only-authorized` invocation,
archive probe, `zstd`, lease, receipt, service change, timer change or schedule
change occurred.

Read-only preflight found the documented dependencies root:root with expected
modes and hashes, host lease state `ready`, inactive/disabled watchdog and
recovery timers, and no scan/lease/receipt artifacts. The private staging
directory was root-owned mode `0700`; staged guard and test files were
root-owned mode `0644`, single-link, and matched the release card hashes.
Target-Linux imports passed. The focused synthetic suite passed **14/14**,
including one denial for each preflight gate with no child launch.

Only `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` was
replaced. The old bytes were checkpointed root-only at
`/var/lib/local-ai-lab/f2-diagnostic-checkpoint-20261018/` before replacement.

| Path/role | SHA-256 | Owner/mode/link count |
|---|---|---|
| installed diagnostic guard | `6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f` | root:root `0644`, 1 |
| retained rollback checkpoint | `d50ee2207bc4185db266ad01af540b9b719397dec3855ee579ee18f983a3535d` | root:root `0600`, 1 |
| manual controller | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` | root:root `0750`, 1 |
| observer | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` | root:root `0644`, 1 |
| producer | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | root:root `0644`, 1 |
| host exclusion | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | root:root `0644`, 1 |
| retained integrity | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | root:root `0644`, 1 |
| fixed source adapters | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | root:root `0644`, 1 |

Postcheck repeated target-Linux imports and all 14 tests. The manual status
remained `ready`; watchdog/recovery timers remained inactive/disabled; no
lease, lock, receipt, scanner, `zstd`, `rsync`, `vzdump`, `pbs-client` or
`proxmox-backup` process was present. The checkpoint remains available for
rollback; rollback was not required.

This is disabled diagnostic infrastructure only. It does not explain the
October 17 failure or authorize a new scan. A later cycle requires a fresh
one-cycle approval and current-cycle backup, TrueNAS, quiet-host and lease
preflight. F2, F3 and F6 remain NO-GO.
