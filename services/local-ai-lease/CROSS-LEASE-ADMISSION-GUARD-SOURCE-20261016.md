# Cross-lease admission guard — source-only checkpoint

**State:** offline candidate. No installed controller, admission route, timer,
watchdog or host lease was changed by this checkpoint.

The full-stop and application-B60 controllers maintained separate state and
lock paths. The full-stop candidate could enter its acquisition path while
application-B60 state existed, and the application controller could enter
while a whole-host lease existed. The application controller also had no
separate existing-state check before its atomic state write, so an orphaned
state file without a lock could be replaced.

The candidates now reject the other lease's state or lock before creating
their own lock or stopping a consumer. They treat broken symlinks as present.
The application controller also rejects its own existing state without a
lock. The full-stop CLI performs the cross-lease check before watchdog and
runtime preflight, and the controller repeats the check at its own boundary.

Source SHA-256:

| File | Digest |
|---|---|
| `lease_controller_candidate.py` | `87f2468e51f5e625c7bf81ae5c6b6aea89be9e93f9a93ac96639a5aee530e4ff` |
| `application_b60_controller.py` | `b1fee28026f208c187910a8f8b357c3f760d0cb0043a1bc0b1c4eb95b0926272` |
| `full_stop_acquire_candidate.py` | `5859aba6cccb8f0eb8a971ccc4e3ff7054c1039482f0838c800ed7a10fc0f791` |

The three focused controller/entrypoint suites passed 37/37. The whole
`scripts/local-ai` suite passed 181 tests with two macOS root-custody skips.
Tests confirm rejection before any stop command or own-lock creation.

**Residual gate:** these are startup checks, not atomic mutual exclusion. A
competing lease could begin between the check and lock creation, and an
archive scan could begin or continue across the same race. The old manual
`acquire --light` controller is not covered by this source change. A later
host release needs a reviewed common exclusion protocol across the observer,
retained producer and every permitted lease entrypoint, plus a bounded
process deadline and backup/load conflict checks. This checkpoint does not
advance F2, F3, F6 or the A1 admission gate and is not an instruction to
replace the currently installed hash-pinned modules.
