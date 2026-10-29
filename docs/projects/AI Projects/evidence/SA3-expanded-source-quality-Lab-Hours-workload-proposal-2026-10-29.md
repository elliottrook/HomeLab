# SA3 expanded-source quality Lab Hours workload proposal — 2026-10-29

Status: **SOURCE CONTRACT PASS; NOT ADMITTED OR SCHEDULED**

The machine-readable proposal SHA-256 is
`19bd2cbd42d39de1730d8feeda701b3a3e62391db5f21dbbe18c51c8629f9927`.
Its fail-closed validator SHA-256 is
`6a295574b00d8b0c59d432c2707fa758bd8dc1f7cfc6330dad9aa1af3f9b20c5`.
The complete focused packet, review and workload-proposal suite passes **27/27**.

The accepted source-only quality packet now has a distinct proposed Lab Hours
identity, `sa3-expanded-source-quality-v1`. It must not reuse either existing
three-request smoke or owner-loss workload identity. The current platform
runner hard-codes those two workloads, a three-request receipt and a 30-minute
rescue point; those controls are correct for their registrations but do not
implement this evaluation.

## Exact workload boundary

The machine-readable proposal pins only the visible packet, packet validator
and one-call/no-retry runner. The answer key, fair scorer and independent-review
receipt are explicitly excluded from runtime. The workload:

- uses the accepted 9B model and binary already pinned by Lab Hours;
- makes exactly 20 sequential requests with no retry, tools, credentials,
  authority or effects;
- limits each request to 120 seconds and the complete workload to 2,700
  seconds;
- requires a booking of at least 3,600 seconds, leaving 900 seconds for
  restoration inside that interval;
- retains the bounded prediction/error artifact root-only at mode `0600`;
- treats any timeout, schema error, count drift or custody failure as NO-GO;
  and
- always restores and validates the accepted production services before the
  booking is closed.

The runtime result cannot qualify D4 by itself. The separate answer key and
model-blind semantic reviews are applied later, outside the model-visible and
Lab Hours runtime boundary. No automatic routing, repair or promotion follows.

## Required platform implementation

The platform owner must implement and independently review a third fixed
registration. It must bind the proposed workload ID to the three pinned runtime
files, run the exact packet through the accepted Lab Hours listener, preserve
the predictions in the root-owned attempt record, and project only a bounded
content-free receipt to the reservation result. The guardian deadline must be
derived from this workload's 2,700-second deadline rather than the existing
three-request smoke's 1,800-second rescue point.

Before any effect, the registered runner must require the exact booking,
authoritative immediate window recheck, whole-host lease, shared operation
lock, installed hashes, accepted model baseline, quiet-host checks and armed
guardian. On every success, failure or owner loss it must stop the lab listener,
restore production and prove the production services and lease are healthy.

No installation, registration, reservation, timer, model call, model change,
restart or production effect is authorized by this proposal. After the platform
registration is installed and validated inactive, Stream A can query the
authoritative ledger for a concrete execution-and-recovery window and request
the separate booking/effect approval.
