# M3 October 30 12:16 35B booking and preflight

The authoritative ledger rejected an earlier start because the completed
11:00 booking still owns its declared execution and recovery interval. It then
reported the complete proposed 12:16–13:31 PDT execution-plus-recovery window
clear. Booking `aster-stream-a-m3-35b-20261030-1216` now reserves the registered,
hash-pinned `m3-joint-semantic-35b-public-v1` workload from 12:16–13:16 with its
fixed 900-second recovery reserve through 13:31.

The installed diagnostic correction has all 32 manifest pins exact. Host tests
pass 14/14 and guest tests pass 4/4. The lease is `ready`; LXC104/110/116,
Aster Agent, accepted 9B llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd`
are healthy; no candidate mount, drain state, lock or 35B process remains.
The enabled Lab Hours dispatcher will claim the booking; no separate ad-hoc
timer or arbitrary command was created.

This is conditional execution, not a pass. The booked runner must still obtain
the whole-host lease and shared operation lock, isolate and restore the stack,
and either retain one valid 24-case public result or a bounded terminal failure.
Automatic routing remains off, no model is promoted, and the sealed holdout is
not opened.
