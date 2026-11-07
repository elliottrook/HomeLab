# M5 K2 shadow fixture preregistration — 2026-11-06

## Outcome

The representative sanitized S0 fixture boundary is fixed before any fixture
or K2 shadow result exists. This prevents reuse of spent development or sealed
evaluation cases and prevents candidate output from influencing labels.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/aster-adaptive/nlu_k2_shadow_fixture_preregistration_v1.py` | `c81799aa2d2464e099241b4fbdeb52899d8c73d9ccdc28c7c0b70da21472ead4` |
| `scripts/aster-adaptive/test_nlu_k2_shadow_fixture_preregistration_v1.py` | `98dd7c22f97daa2e7e97858218058f59449f3e925b895082f7f697a8b3d32a96` |
| canonical preregistration | `4f96d441256f07e9d87d709aac20ee8e1f3af50f82c7de15064f0d4b71fb9108` |

## Fixed boundary

The private fixture must contain exactly 60 unique sanitized S0 cases, ten per
request family. It may contain no personal/secret material, credentials or tool
arguments; public evidence retains only request digests. Text and case IDs must
have zero overlap with the exact development corpus and independently sealed
evaluation.

Fixture custody and label review must be performed by distinct reviewers.
Labels must be completed before candidate collection, with candidate output
hidden from the reviewer. A later B60 collection needs its own Lab Hours booking
and production-restoration proof; it is fixed at 60 requests, zero retries, no
route/provider effect and zero external cost.

## Verification

- focused tests: 4/4 passed;
- syntax compilation: passed;
- overlap, privacy, reviewer-independence and no-effect requirements are exact;
- fixture creation, label review, model call and route effect: none.

The actual independently custodied fixture and reviews remain open and may be
created only after K2 passes development and sealed qualification.
