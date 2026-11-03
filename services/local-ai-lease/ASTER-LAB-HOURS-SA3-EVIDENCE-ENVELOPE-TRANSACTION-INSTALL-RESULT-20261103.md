# SA3 evidence-envelope transaction inactive install result — 2026-11-03

Status: **PASS AFTER FAILED-CLOSED V1 — CORRECTED V2 INSTALLED INACTIVE**

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

Jason directed Stream A to continue without routine approval prompts. The
corrected v2 transaction then installed successfully. Independent postcheck
matched both dormant host modules, the guest wrapper and the release manifest;
host and guest imports passed, both v2 rollback checkpoints are root-only, no
candidate unit exists and `sa3-evidence-envelope-quality` remains absent from
the effectful registered-runner kinds. Aster Agent, accepted llama.cpp/SYCL,
Speech, the Lab Hours control timers, `pvescheduler` and `pvestatd` remained
active.

Inactive target-Linux installation is complete. The next source-only item is
the exact runner activation packet. No booking, schedule, lease, service stop,
restart or model call is authorized by this result.
