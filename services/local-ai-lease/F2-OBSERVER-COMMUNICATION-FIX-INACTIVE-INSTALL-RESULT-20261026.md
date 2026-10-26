# F2 observer communication fix — inactive installation result

**Result:** PASS after one verified rollback and corrected test packaging.

Jason approved the exact one-file inactive installation from card commit
`a46b004f94fc7d4a3fd4038125615266b8c8b564`. Source commit was
`d00073e542aaebc816ddee31ae3a94fa3caacf07`.

## Transaction result

The first transaction installed the candidate and passed the installed focused
suite 15/15. The broader suite then reported nine missing-fixture errors because
the clean archive contained `scripts/local-ai` but omitted historical service
units and cards read by those tests. The error trap restored the predecessor.
Read-only verification confirmed predecessor SHA-256 `9efe6e5d…e8a1`, unchanged
October 26 terminal-state SHA-256 `51e296ea…de6`, disabled/inactive timers,
ready lease state and healthy production.

The source archive was rebuilt from the same clean source commit to include
both `scripts/local-ai` and `services/local-ai-lease`. The resumed transaction
then completed:

| Check | Result |
|---|---|
| Installed coordinator SHA-256 | `6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193` |
| Installed custody | `root:root 0644`, regular, one link |
| Installed default-launcher assertion | `final.__kwdefaults__["popen"] is None` |
| Focused installed coordinator suite | 15/15 passed |
| Broader clean target-Linux F2 suite | 51/51 completed: 50 passed, one expected skip |
| Preserved October 26 state | unchanged SHA-256 `51e296ea…de6`, `root:root 0600`, regular, one link |
| Recurring F2 timers | disabled and inactive |
| October 26 exact-date timers | absent |
| Scanner, `zstd`, lease, lock and receipt | absent |
| LXC104/110/116 and Aster/llama.cpp/Speech | running/active |
| News timers and Proxmox daemons | active |

The successful rollback checkpoint is
`/root/f2-observer-launcher-fix-rollback-d00073e5-retry1`; the first failed
attempt and its restored predecessor remain separately preserved under the
corresponding non-`retry1` root-only paths.

A transient `/proc/<pid>/comm` disappearance was printed during a postcheck
because a process exited between directory enumeration and read. The script's
guard explicitly continued on that race, all bounded postchecks completed and
the independent postcheck repeated them cleanly.

## Boundary

No F2 timer or scan ran, no receipt or lease was created, no consumer stopped
and no model was called. This result admits preparation of a fresh exact-cycle
card only; it does not authorize that activation or retry the spent October 26
cycle.
