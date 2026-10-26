# F2 observer communication root cause — 2026-10-26

The October 26 F2 failure was caused by an internal process-launch API mismatch,
not by a missed timer.

The exact-date preparation and final timers ran at 01:15 and 01:20 PDT.
Preparation passed. In the installed and source coordinator,
`final()` defaulted its launcher to `subprocess.run`. That call blocks until the
observer child returns and yields a `CompletedProcess`. The coordinator then
treated that completed value as a live `Popen` process and called
`process.communicate(...)`. `CompletedProcess` has no `communicate` method, so
the resulting `AttributeError` was reduced to the bounded class
`OBSERVER_COMMUNICATION_FAILED`.

The existing success test did not exercise this installed entrypoint. It
injected a fake Popen-like result that implemented `communicate`. Tests that
used the real default stopped earlier at deliberately failed final-guard
checks. Target-Linux validation reused the same synthetic boundary, while hash
validation could only prove that the reviewed bytes were installed. The test
suite therefore confirmed the mocked contract rather than the systemd contract.

The observer child was launched before the coordinator fault. Its output and
return code were not processed, so the evidence can establish only that no
accepted archive result was retained. It cannot prove that no archive check
began. Postchecks found no remaining observer or `zstd` child and production
was healthy.

The correction must use one consistent process API, retain the existing
timeout and process-group termination behavior, and add a regression that
exercises the default launcher used by `main()`/systemd. Offline and target-
Linux installed-path proof are required before a fresh exact-cycle card. The
spent October 26 cycle must not be retried.
