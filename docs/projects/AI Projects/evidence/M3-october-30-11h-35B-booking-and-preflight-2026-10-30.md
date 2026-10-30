# M3 October 30 11:00 35B booking and preflight — 2026-10-30

After the 10:30 transaction produced a specific bounded residency failure,
restored production and its stable-holder correction passed target tests, the
authoritative ledger reported the complete 11:00–12:15 PDT window clear.
Exact workload `m3-joint-semantic-35b-public-v1` is separately booked as
`aster-stream-a-m3-35b-20261030-1100` from 11:00 to 12:00 with recovery
reserved through 12:15.

Static preflight finds all 32 corrected installed pins exact, whole-host lease
ready, no mount/process/drain/operation state, and healthy Doctor and
production. Stream A is supervising this run in the active thread. Runtime
reservation, lease, shared-lock, health and quiet-host gates remain fail
closed. No model promotion, calibration/holdout access or automatic routing is
authorized.
