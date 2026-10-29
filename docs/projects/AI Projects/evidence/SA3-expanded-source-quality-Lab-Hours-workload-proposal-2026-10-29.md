# SA3 expanded-source quality Lab Hours workload proposal — 2026-10-29

Status: **SOURCE CONTRACT PASS; NOT ADMITTED OR SCHEDULED**

The dependency-closed machine-readable proposal SHA-256 is
`c268c718df86e7d627537d4047c6b0fc0bef7bc5129ab280e4c8d340f57b9a53`.
Its fail-closed validator SHA-256 is
`64fa3069c34bae41684411a9c3deac9741b02b22b5eba08daab7df95f20b3bb7`.
The complete expanded-quality source suite passes **31/31**.

The accepted source-only quality packet now has a distinct proposed Lab Hours
identity, `sa3-expanded-source-quality-v1`. It must not reuse either existing
three-request smoke or owner-loss workload identity. The current platform
runner hard-codes those two workloads, a three-request receipt and a 30-minute
rescue point; those controls are correct for their registrations but do not
implement this evaluation.

## Exact workload boundary

The machine-readable proposal pins the visible packet, packet validator,
one-call/no-retry runner and the fair scorer required by the validator's module
import. The scorer was already included in the accepted independent review and
has no answer-key content; the runtime never invokes it. The answer key and
independent-review receipt are explicitly excluded from runtime. The workload:

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
registration. It must bind the proposed workload ID to the four pinned runtime
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

## Platform registration result

The platform owner subsequently completed the source registration at commit
`53c81e1c`; the [reconciled result](SA3-expanded-source-quality-Lab-Hours-registration-result-2026-10-29.md)
passes 17/17 focused tests and preserves the four-file dependency closure.
It remains deliberately NO-GO before any production drain because the distinct
SA3 owner transaction is not implemented or installed. That transaction and
its inactive target validation are now the next gate; no window should be
checked or booked yet.
