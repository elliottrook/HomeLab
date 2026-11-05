# D4 candidate-j R1 NO-GO, correction and R2 schedule — 2026-11-04

R1 claimed exactly at 21:00 and ended terminal NO-GO at 21:03:07 with
`first_failure_phase=owner-transaction`,
`failure_code=OWNER_TRANSACTION_FAILED_RESTORED` and production restored. No
model request ran. The wrapper incorrectly rejected expected inert
candidate-g/i packet files in the shared runtime directory before transport.

The bounded correction removes only those two predecessor packet names from
the existence ban. Review/decision material remains forbidden, candidate-j's
five-file pins remain isolated, and automatic routing/authority remain off.
The corrected wrapper installed inactive on host and guest at `a883c144…5f2a`.
The installation preserved the concurrent EPUB alignment additions in the
41-pin release manifest, restarted no service and left the lease ready with no
state or locks.

The ledger rejected 22:00 because AsterTV alignment owns 22:15–22:45 plus
recovery through 23:00. Fresh booking
`aster-stream-a-sa3-candidate-j-20261104-2300-r2` therefore uses the first
complete clear window, 23:00–23:45 (`-07:00`). R2 remains conditional on all
fresh runtime gates and must produce six valid rows, exactly two model requests,
zero retries/errors/effects and complete production restoration.
