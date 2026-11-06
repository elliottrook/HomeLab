# SA4 post-install first-repair release candidate — 2026-11-05

The fresh v4 release packet binds the first supervised canary repair to the
independently validated runtime-control installation result
`10895012…32b`, the exact five installed transaction sources, plan
`59641703…956`, drifted target `19b4e02d…df1a` and candidate
`4529dee5…1065`.

The retained canonical packet digest is
`f08027af9b184cba0c484925832da0b5290e3550513c8a81f69a00fc641153a0`.

The correction is no longer caller-asserted: the root transaction owner must
exclusively create the real operation lock and plan-bound emergency stop at
runtime, verify them before every phase, and retain them on uncertainty. The
release also requires a fresh measurement, exclusive checkpoint, absent-then
single-use ledger, independent postcheck, production postcheck, current
installed-hash recheck and a ready whole-host lease.

No authority is embedded. The prior approval and every prior ceremony grant
are explicitly non-reusable. A run requires a new unique AI-PAM one-use grant,
a new exact-plan owner proof and intersecting fresh deadlines. Limits remain
one repair, at most one rollback, zero automatic retry, no service restart,
automatic routing off and no automatic promotion.

The packet is effect-ineligible and does not sign, claim, checkpoint, repair or
invoke the installed owner. Its five focused tests and the complete 163-test
SA4 suite pass. It is ready to be presented for the new exact repair gate.
