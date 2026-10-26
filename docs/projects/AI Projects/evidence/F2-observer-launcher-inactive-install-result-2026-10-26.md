# F2 observer launcher inactive-install result — 2026-10-26

**Decision:** PASS for inactive installation; no timed test is scheduled.

The corrected coordinator from platform commit `d00073e5` is installed at
SHA-256 `6a1d520a…8193`, `root:root 0644`, regular with one link. Its installed
default-launcher assertion is true, the installed focused suite passed 15/15,
and the broader target-Linux F2 suite completed with 50 passes and one expected
skip out of 51 tests.

The first transaction attempt passed the focused suite but its broader test
archive omitted historical fixtures. The rollback trap restored exact
predecessor SHA-256 `9efe6e5d…e8a1`. After independent rollback verification,
the archive was rebuilt from the same source commit with the missing repository
fixtures and the approved transaction resumed successfully. This was a test-
packaging failure, not an F2 scan or coordinator regression.

Independent postchecks matched installed hash/custody and preserved the October
26 terminal-state digest `51e296ea…de6`. Recurring timers are disabled and
inactive; exact-date timers are absent; no scanner, `zstd`, lease, lock or
receipt exists. LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
News timers, pvescheduler and pvestatd are healthy.

Platform evidence is committed at `d82ad6c5`. This closes the inactive install
and target-Linux proof. A fresh date-specific card, independent review and
separate activation approval are required before another timed attempt.
