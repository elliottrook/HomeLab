# F2 fixed preflight wrapper — disabled-install card

Status: source-only candidate; not installed, scheduled, or run. This card
does not authorize an F2 scan, receipt, lease, timer, service change, or
remote push.

## Exact candidate and rollback

Install only the two entrypoint modules below into the existing root-only
directory. Tests are private evidence and are not installed. The live
dependency pins are read-only prerequisites, not files to replace in this
stage.

| Source | SHA-256 | Target path/mode | Prior state |
|---|---|---|---|
| `f2_preflight_snapshot.py` | `a2324d6a5ba4869778713319a511acc207f1d8332dd1af7e4520be382cfe02fa` | `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py`, root:root 0644 | absent; checkpoint absence |
| `f2_preflight_fixed_wrapper.py` | `2b381465300db3d7cc1d521123665df19ff58fad12d5cccd54720b9f89cb433c` | `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py`, root:root 0644 | absent; checkpoint absence |

The source uses the real existing `host_exclusion` flock rooted at
`/var/lib/local-ai-lab`; it does not create or read a synthetic exclusion
token. The snapshot directory is `/var/lib/local-ai-lab/f2-preflight`,
root:root mode 0700, and the snapshot is created atomically as root:root
0600 only by the wrapper after successful preflight. No snapshot exists in the
candidate state.

Before any write, verify the target parent and all six fixed dependency pins:

| Dependency | Required SHA-256 |
|---|---|
| `f2_observer_runner_candidate.py` | `6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f` |
| `retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` |
| `retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |
| `/usr/local/sbin/local-ai-lease` | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` |

Rollback removes only the two newly added modules and the empty preflight
directory, or restores captured prior bytes if a target unexpectedly existed.
Do not remove the shared `/var/lib/local-ai-lab` root or alter the existing
manual helper/dependencies.

## Disabled-stage procedure

1. Verify the exact old state, parent custody, dependency pins, and absence of
   the two target files and `f2-preflight` directory.
2. Copy only the two pinned modules, preserving root ownership and 0644 mode;
   create only the 0700 `f2-preflight` directory if absent.
3. Run target-Linux imports and the pinned source/test suite from a private
   copy. Run root-custody positive tests on Linux; macOS skips are not
   sufficient evidence.
4. Recheck no systemd unit/timer, receipt, snapshot, listener, lease, process,
   service state, schedule, GPU state, archive, TrueNAS task or model request
   changed. The wrapper remains uncalled and no timer is enabled.

The wrapper owns the current host clock, local cycle, snapshot path, complete
pin map, and real host exclusion. It performs the slow task-1/artifact/mirror
preflight before the 01:10 boundary; the final guard requires the 01:10–01:19
window, current lease readiness, absence, quiet host, suitable load, all pins,
and an actually held `host_exclusion` flock. This is not an F2 result or F3
receipt release.
