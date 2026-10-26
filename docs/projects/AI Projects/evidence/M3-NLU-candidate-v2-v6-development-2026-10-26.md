# M3 NLU Candidate v2–v6 development — 2026-10-26

> Decision: **CANDIDATE V6 DEVELOPMENT PASS; FRESH CALIBRATION REQUIRED**

Candidate v1's sealed calibration rejected the candidate because its prompt
contradicted its output contract: “Never claim a route” suppressed the
evaluation-only `route` label. The rejected private calibration was not used
for prompt tuning. Candidate revisions used only the exposed 24-case synthetic
development fixture and the accepted local Qwen3.5-9B/SYCL service.

| Candidate | Valid | Exact | Unsafe false route | Privacy underclassification | Decision |
|---|---:|---:|---:|---:|---|
| v2 | 15/24 | 0/24 | 1 | 0 | reject |
| v3 | 17/24 | 13/24 | 2 | 0 | reject |
| v4 | 22/24 | 16/24 | 1 | 1 | reject |
| v5 | 22/24 | 19/24 | 0 | 1 | reject |
| v6 | 23/24 | 23/24 | 0 | 0 | development pass |

Candidate v6 also has zero unnecessary non-routes. Its one invalid result is
the deliberately ambiguous change request; strict parsing keeps that result
non-routable. Output SHA-256 is
`4608be907790e2b87621764b509c69f005184cffc9a975ef38f0654815048fcf`.
The tested prompt was then flattened into a standalone adapter without changing
its 3,260 bytes or SHA-256
`ed4031e1cfb6cd5d1670775e854552c4017da1d2829e1a4fa0e7608e30c0ad5c`.
The frozen standalone adapter SHA-256 is
`eb94d448e4c9a54a95df9660dfdf6bf875011def4c72767942182faccdd73655`
and its bounded development runner SHA-256 is
`35b198b1385a14dc5350f70a38dd0a52fb6b628cbcccd0c2c509551ab91790a4`.
The content-free policy SHA-256 is
`45eeba30077b2c2146f08196ce591ec9d89ce8a8465cfa654bd2d28913530bb0`;
the sealed candidate artifact SHA-256 is
`6a16f92527981d5048a4163b5c8de2ad146ec7901f459d221f628e663d06c236`.

All requests were local, sequential, temperature zero and tool-free. The model,
Aster Agent, Speech and News remained healthy and no service restart occurred.
No development result grants routing, tool access or production authority.

Candidate v6 must now be sealed with its exact adapter, prompt-policy and
runtime identities. Because Candidate v1's calibration was opened and scored,
v6 requires a newly created and independently labelled calibration release.
The existing independent holdout remains unopened and cannot be repurposed for
candidate selection.
