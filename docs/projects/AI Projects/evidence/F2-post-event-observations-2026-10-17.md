# F2 October 17 — post-event observations

**Evidence class:** read-only post-event observations. These observations do
not reconstruct the 01:10 failure, prove that an archive scan ran, authorize a
retry, or change the cycle decision.

After the one approved guard invocation returned `F2NoGo` without archive
rows, the following later observations were recorded:

- Proxmox `local-ai-lease status` remained `ready`.
- The installed producer's final-line parser matched each fixed 104/110/116
  guest log successfully.
- The fixed October 17 `pvescheduler` journal filter returned exactly two
  rows for the backup job: one start and one success, with no task error.

These observations narrow current source-shape concerns but cannot identify
the failed predicate or observer stage at 01:10. The October 17 approval is
consumed; F2 remains **FAILED/UNKNOWN**. No retry, drill, A1 run, lease,
receipt or production change is authorized by this record.
