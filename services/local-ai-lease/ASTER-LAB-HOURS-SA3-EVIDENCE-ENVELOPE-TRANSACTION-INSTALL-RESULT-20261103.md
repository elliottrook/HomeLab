# SA3 evidence-envelope transaction inactive install result — 2026-11-03

Status: **NO-GO, ROLLED BACK; CORRECTED V2 READY**

The approved v1 bundle entered the fixed inactive installer and failed at the
guest import postcheck. The new wrapper imported
`aster_llama_sa3_guest_wrapper` as a Python module, but the earlier wrapper is
installed as `/usr/local/sbin/aster-llama-lab-sa3`, not in the guest runtime
module path. The bounded failure was `GUEST_IMPORT:ModuleNotFoundError`.

The transaction never activated its runner, created a booking, acquired a
lease, stopped a service or called a model. Host and guest targets rolled back
to absence, the prior release-manifest digest was restored, both v1 root-only
checkpoints were retained and all production services remained active.

Platform commit `1b471579` makes the candidate-g wrapper self-contained and
uses a fresh v2 checkpoint/bundle identity. The 58-test suite passes. A direct
target-Linux import from a fixed temporary path passed and the temporary files
were removed. Two corrected seven-file bundles match at SHA-256
`b7e415c2cdacdd7227b362e8dec48cf6506690824a7deba189d8c5c3700a0bb5`.

The corrected hash is a new installation packet and therefore requires a new
explicit approval. No retry has occurred.
