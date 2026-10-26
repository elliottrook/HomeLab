# M3 NLU post-journal deadline correction — 2026-10-25

Result: **SOURCE PASS / STAGED PACKET SUPERSEDED**

The calibration runner previously calculated its request timeout before the
durable `attempt_started` journal write. A slow journal flush could therefore
consume the remaining 1,200-second wall budget while leaving a stale positive
timeout, allowing a model request to start after the declared run deadline.

Commit `682608d2` now recomputes the remaining wall budget immediately after
the durable attempt-start boundary and before opening the HTTP request. If the
budget has expired, it records a content-free `deadline_exceeded` result and
starts no request. A regression test advances the clock across the deadline
between the first budget check and request-open boundary and proves that the
transport receives zero calls.

Validation:

- 116 dependency-free NLU tests passed;
- corrected runner SHA-256:
  `a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f`;
- corrected staging manifest SHA-256:
  `05aa0f287795dacfa72c37d7b275a85f67e96f0cc253225dcf78908585970e19`;
- corrected staging validator SHA-256:
  `487341d1d35fa7ee313aeb76816162048e2402a985a801f6053e3ea89a971e80`.

The existing eleven-file LXC110 directory remains inert and owner-only, but it
contains the superseded runner and manifest. It must not be used for a model
call. A bounded inactive replacement and target-Linux validation are the next
gate. No private cases were read, no lease was acquired and no model request,
route or service change occurred.
