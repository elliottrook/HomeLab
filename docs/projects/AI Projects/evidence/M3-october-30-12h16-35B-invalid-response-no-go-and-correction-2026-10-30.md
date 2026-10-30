# M3 October 30 12:16 invalid-response NO-GO and correction

Booking `aster-stream-a-m3-35b-20261030-1216` ran once and failed closed after
all 24 requests. The bounded transaction projection records `attempted=24`,
`valid=0`, `first_record_failure=invalid_response` and
`production_restored=true`. No public result was retained and the holdout
remained sealed. Independent postcheck found the lease ready, no drain state,
lock or candidate mount, all three guests running, and Aster Agent, accepted
9B llama.cpp/SYCL, Speech and Proxmox daemons healthy.

The evidence localizes the defect to response parsing, after successful model
transport. The 35B service was intentionally reasoning-enabled and its message
envelope may add `reasoning_content`. The parser passed that whole envelope to
a strict final-answer boundary which accepts only `role` and `content`, so the
extra private field caused every completed response to be invalid.

Platform commit `8747d6ad` validates exactly an optional string-or-null
`reasoning_content`, discards it, and constructs a new `role`/`content` envelope
for the existing strict answer parser. No hidden reasoning is parsed or
retained; any other field still fails closed. It also prevents the guest's
nested failure code from overwriting the transaction failure code, so later
terminal evidence remains specific.

The source suite passes 24/24 and all 32 pins match. Inactive installation at
platform commit `66ca6faa` passed 14/14 host and 2/2 guest target tests with
production healthy and no restart or model call. The spent booking was not
retried. A fresh booking is required for another public-gate run; automatic
routing and model promotion remain off.
