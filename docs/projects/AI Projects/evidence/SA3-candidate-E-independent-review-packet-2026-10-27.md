# SA3 candidate-E independent review packet — 2026-10-27

Candidate E's independent review inputs are now content-minimized and
machine-verifiable. The packet includes exact source and freeze commits, SHA-256
pins for the two candidate modules, fresh packet and result, the eight bounded
result rows, and an offline validator.

The validator recomputes all four file digests, requires the exact result
schema, verifies the 8/8 aggregate and healthy postcheck, and compares every
observed disposition/target/kind/citation count with the expectation frozen in
the fresh packet. It rejects duplicate JSON keys, missing/duplicate cases,
extra result fields, changed digests and semantic disagreement. Its own tests
pass **2/2**, including a rehashed but semantically altered result fixture.

The review packet contains no credential, prompt response prose, private
reasoning, raw evidence reference or production incident. Running:

`python3 -B services/aster-agent/evals/sa3_candidate_e_review.py`

returns exactly a passing candidate ID, four verified files and eight verified
cases in the current checkout.

## Pins

| File | SHA-256 |
|---|---|
| `services/aster-agent/evals/sa3-candidate-e-review-manifest.json` | `941d0d0bd8ac7c21db18d71ede18f8a4a0131194632f2ff290e0846b40d4851e` |
| `services/aster-agent/evals/sa3_candidate_e_review.py` | `62bbdf549e1d50885ac239b3454a7442e4c2b7cbd222801ce8565f53f082ce33` |
| `services/aster-agent/evals/test_sa3_candidate_e_review.py` | `7a3fe5ec8463fd75fdfedc3ce6537e700be59a6b8d99019ad05178a7b8b3e27e` |

This prepares independent review but does not perform it. Representative SA3
acceptance remains open until a separate reviewer verifies the pinned packet
and records a result. Deployment and runtime authority remain closed.
