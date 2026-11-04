# SA3 candidate-i first inactive-install attempt — NO-GO — 2026-11-04

The first inactive-install attempt failed before checkpoint creation or any
target write with bounded code
`CUSTODY:lab_hours_reserved_runner.py`. The card had correctly pinned the
installed bytes but incorrectly described the executable reserved runner and
full runtime as mode 0644; both exact installed files are root:root, one link,
mode 0755.

Independent absence checks confirmed that no candidate-i host or guest target,
checkpoint, booking or unit was created and the lease remained ready. The
source correction changes only those two expected/preserved modes to 0755 and
adds a regression assertion. It does not reuse the failed archive identity.
A fresh deterministic archive and the same exact predecessor preflight are
required before a new inactive-install attempt.
