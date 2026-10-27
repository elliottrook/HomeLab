# F2 Proxmox path install and daytime real scan — 2026-10-27

## Result

**PASS at the installed and real archive-probe boundaries.** This is readiness
evidence for a fresh exact-clock cycle; it is not itself retained F2/F3
admission evidence because the daytime run used a synthetic 01:20 clock and a
no-op receipt writer.

The first three-file installation attempt failed before running tests because
the packet invoked `unittest` with filenames instead of module names. Its trap
restored all three exact predecessors. The corrected command then installed
platform source `18c7198e`, passed 60/60 target tests and passed two identical
installed no-scan rehearsals across VMIDs 104, 110 and 116.

Installed pins:

- observer runner `ce2332a1…4157f`;
- fixed preflight wrapper `e072e907…109d0`; and
- daytime rehearsal `20f35267…ff32`.

The offsite relay and EPUB narration worker were paused to remove competing
load; Aster Speech itself stayed active. The production archive observer was
then run under an independent 20-minute wall bound with the current completed
backup cycle, actual `ionice -c3 nice -n 19 zstd -t --quiet` probes and a no-op
receipt writer.

| VMID | Size | Elapsed | Exit |
|---|---:|---:|---:|
| 104 | 1,998,381,868 bytes | 19.312 s | 0 |
| 110 | 43,638,927,627 bytes | 337.578 s | 0 |
| 116 | 4,361,697,775 bytes | 42.015 s | 0 |

All three fixed current-cycle archives passed in about 399 seconds of probe
time, within every per-file bound and the 20-minute outer envelope. No receipt,
lease or lock remained and no `zstd` child survived. The offsite relay and its
timer were restored; the narration timer and worker were restored, with the
worker resuming in `activating` state. Aster Speech stayed active.

This closes the archive process, path and timing uncertainty during daytime.
The remaining proof is the actual 01:15/01:20 clock/timer path against the next
fresh backup cycle. It must still fail closed on any changed runtime gate.
