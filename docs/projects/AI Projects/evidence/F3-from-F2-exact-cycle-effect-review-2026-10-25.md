# F3-from-F2 October 26 effect-card review

**Date:** 2026-10-25

**Decision:** design **GO**; effect **NOT AUTHORIZED**

The platform owner reviewed local platform commit `0b74e6e8` independently.
The review accepted the October 26 effect-card design because it pins the
installed four-file call graph, requires independent exact-cycle F2 success
and cleanup, permits one invocation with no retry, preserves uncertain
receipts, independently verifies the post-write receipt, and defers F4 to a
subsequent fresh backup cycle.

The card and converter, installation-card, retained-integrity and F2 suites
pass 31/31 locally. The installed converter separately passed its 27/27 target-
Linux suite and remains inert.

This review does not invoke F3, write a receipt, alter F2 timers, acquire a
lease, stop a service, call a model or authorize F4. The next decision is one
exact conditional effect approval after tonight's F2 outcome; a failed,
partial or uncertain F2 result must produce NO-GO without invoking F3.
