# M3 K2 shortlist arbitrator source — 2026-11-06

**State: source-only; no transport or model call.**

The K2 arbitrator now has an exact request and response boundary. It accepts
exactly four unique IDs from the frozen 16-label ontology, exposes only those
four content-free label definitions to the accepted production 9B identity,
and requests one temperature-zero, seed-pinned JSON selection. The request has
no tools and the parser rejects unknown IDs, extra fields, duplicate keys,
multiple choices, incomplete responses and free text.

The selected coherent label is passed through the existing tightening-only
deterministic guard. The content-free record contains the case ID, shortlist,
selected ID, guard-change flag, guarded interpretation and latency; it never
contains request or response text. Authority remains `not-granted`.

This source does not perform transport, access the accepted corpus, open the
sealed evaluation, acquire a lease, book Lab Hours, stop/restart a service,
change a model/backend, enable routing or promote a candidate.

Frozen source evidence:

- arbitrator SHA-256:
  `7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962`
- focused test SHA-256:
  `7c1cb75e70a02d73eded6b243e6ff5305722f54a97ea1307b3393377bd2df6f3`
- K2 preregistration/arbitrator tests: `11/11` passed
- syntax compilation: passed with an isolated bytecode cache

## Shortlister source and Mac-local preflight

The fixed Swift shortlister was frozen before reading validation labels. It
uses the macOS English 300-dimensional word embedding, normalized mean token
vectors and per-label training centroids, then emits exactly four candidates.
It requires the accepted `768/192`, 16-label corpus shape, refuses symlinked
input and existing output, and restricts its create-only result to mode `0600`.

- accepted corpus SHA-256:
  `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`
- final shortlister source SHA-256:
  `08c720b1cd1d1a78825e9229547795298a4a220f608b0385588e81bf7f185e39`
- source test SHA-256:
  `970385e152ac21b267c3de9d7f74b4467a7c8a1444170e03ad598694c46806c8`
- compiled binary SHA-256:
  `b26309bc7ee3d0768d5e1355920c69cd54b02563920fafbe63d407a73077575e`
- macOS: `26.6.2`
- Swift: `6.4.2`, target `arm64-apple-macosx26.0`
- embedding dimension: `300`
- validation rows: `192`
- top-1 exact: `125/192`
- top-4 recall: `179/192`
- final content-free shortlist artifact SHA-256:
  `620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e`
- final artifact custody: one regular file, mode `0600`, 192 unique IDs,
  exactly four unique candidates per row
- combined K2 source tests: `14/14` passed

The first create-only preflight produced identical bytes but inherited mode
`0644`. It was retained, not treated as a release artifact, and the source was
tightened before the final preflight. No request text is in either output.
The final artifact has identical bytes and correct owner-only custody.

The measured 93.2% shortlist recall clears the structural feasibility gate:
the arbitrator can see the correct label in 179 cases, leaving headroom above
the 116-decision policy floor. This is not evidence that arbitration passes;
no model call has yet occurred.
