# Stream A evaluation watchdog/recovery inactive installation — 2026-10-25

> Result: **PASS; installed inactive**

Jason approved the exact thirteen-artifact inactive installation from
implementation `780c33e2471536ff0f3eb699a9dba93274808919`, metadata/card
`75b423d43c00611681c5e68ed07e3535c171ceb2`, and corrected transaction
metadata `525fc56fb7ed256676ed234b1913a4d5d18d03b2`. The card SHA-256 is
`78fd2388168c464877c20b7abab3f99f042bb553de38f7f56d46227ef8d99210`;
the transaction-card SHA-256 is
`4ae9477bcdb58e600a58b7acb764d1fcd63e0568a0225fb263bfc2b43ce3225d`.

## Transaction result

Fresh preflight matched the six installed evaluation-entrypoint dependency
hashes, found every candidate target absent and found no lease, lock, identity,
intent, heartbeat, status or restore state. The first copy attempt rolled back
all thirteen exact candidate files after the Stream A transaction harness
incorrectly invoked the inert wrappers with no functional argument. The source
card requires the normal inert argument shape—owner `--run` and
heartbeat/watchdog `--once`—while omitting `--effect-authorized`. This was a
local validation-harness error, not a packet defect. Independent postcheck
confirmed exact target absence and healthy production before retry.

The corrected harness changed only those three inert invocations. The second
transaction passed:

- 51/51 focused target-Linux tests;
- installed-path imports with Python `-B`;
- exact effect-disabled output from all three inert wrappers;
- static `systemd-analyze verify` for all five units/timers;
- exact SHA-256 for four Python files, four wrappers and five unit/timer files;
- no `__pycache__` or `.pyc`; and
- no runtime state, identity or observation file.

Independent postcheck found the owner service, owner-heartbeat service/timer
and watchdog service/timer all `disabled` and `inactive`. `local-ai-lease`
remains `ready`; LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are healthy. The October 26 F2 preparation and
final timers remain enabled and active for 01:15 and 01:20 PDT.

## Effect boundary

No daemon reload, unit enable/start, owner identity, lease acquisition,
consumer stop, restore observation, model request or F2 action occurred. The
inactive installation closes the F6 staging dependency only. A separately
reviewed activation must still create an identity safely, prove read-only
healthy-lease behavior, arm the independent watchdog/heartbeat boundary and
retain exact recovery rollback. Fresh F2/F3/F4 evidence and a separate live
D4/M3 evaluation authorization remain required.
