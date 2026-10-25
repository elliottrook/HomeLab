# M3 NLU staging dependency-closure correction — 2026-10-25

> Result: **CORRECTED PACKET PASS; LIVE RESTAGING NOT YET AUTHORIZED**

The first approved inactive LXC110 staging attempt validated the exact private
ten-file packet and its root-only custody, then failed closed before the atomic
rename. Importing `nlu_calibration_release.py` required the local
`nlu_candidate_bundle` module, which the frozen packet did not include. The
transaction removed its new incoming and parent directories. A read-only
postcheck found Aster, Speech and the accepted llama service still active.

The source dependency closure has one additional file:

| Input | SHA-256 | Bytes |
|---|---|---:|
| `nlu_candidate_bundle.py` | `5a797b2f0166d6ead276c0487887074ea1f78396d2ddfcd4ea7d6915df36e156` | 4,802 |

The corrected manifest pins eleven inputs and has SHA-256
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
The owner-only Mac packet passed exact-name, regular-file, digest and aggregate
byte validation: 11 inputs and 98,414 bytes. All eight staged Python modules
then imported with bytecode writes disabled. The focused manifest and candidate
bundle suites passed 14 tests.

This correction changes only the inactive packet definition. It grants no
route or inference authority and does not authorize a copy to LXC110, a lease,
model request, scoring, threshold selection, service change or Git push. The
next live step is a separately approved restaging of this exact corrected
packet.
