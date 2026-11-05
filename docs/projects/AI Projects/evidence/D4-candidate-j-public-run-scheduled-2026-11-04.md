# D4 candidate-j public run scheduled — 2026-11-04

Candidate-j R1 is scheduled for the first authoritative conflict-free window:
2026-11-04 21:00–21:45 host time (`-07:00`), booking
`aster-stream-a-sa3-candidate-j-20261104-2100-r1`. The earlier candidate window
was not used because EPUB narration owns 20:00–20:45 plus recovery through
21:00. The ledger returned `clear` for the complete candidate-j execution and
recovery window before the booking was created.

Static preflight passes at Stream A commit `3374d77b` and platform evidence
commit `f0b73045`: candidate-j is installed inactive with exact hashes, the
lease is ready, state/locks/processes/units are absent, dispatcher and Doctor
are active/enabled, and production services/schedules are healthy. The run is
conditional on all fresh claim-time gates and accepts only a six-of-six,
zero-error/effect result with exactly two model requests and complete production
restoration. Failure is terminal without retry.

This is one bounded public-development run, not a release. A passing result is
required before an independent custodian may create an untouched quality
packet. It grants no route, authority, tool, repair, restart, model/backend
change or automatic promotion.
