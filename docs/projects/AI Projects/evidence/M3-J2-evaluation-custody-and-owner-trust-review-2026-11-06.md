# M3 J2 evaluation custody and owner trust review — 2026-11-06

## Evaluation result

**PASS — accepted sealed-evaluation custody evidence.** The revision-5 return
contains exactly the five named content-free files. Their independently
recomputed SHA-256 values match the custodian report:

- evaluation public key:
  `46685b0ebd4e1bcf65bfae35df4858373b2f928fe3f81ab267bfa58cedfa9498`;
- evaluation custody receipt:
  `0600a78eadb171fe710764a47ea8c549e9180a112ac05bdea91bcecc0353ddc3`;
- evaluation custody proof:
  `912a87368315a1fe64d390a94dc9fb25c7dbf53dbdff795def6a2132991261cb`;
- disjointness receipt:
  `05da5fa23f203d773101567c78bb31f431c0ec3b1049de2e729c323f0af007f0`;
- disjointness proof:
  `27bbc168b347c6839fe3200c46c0cf582ae3d08f856caece8ab83c3299b68fc6`.

The exact evaluation receipt validator passes at 32 cases, 16 labels, two per
label, sealed before training, trainer access forbidden and no returned
content. The signed disjointness receipt binds the accepted 960-row corpus and
the same evaluation/evaluation-set digests with exact-set intersection zero.
Both RSA signatures verify against the evaluation key. The evaluation key is
distinct from the accepted corpus key. Stream A did not read the sealed
evaluation.

## Complete-chain candidate

The real corpus release, retained owner corpus acceptance, frozen recipe,
accepted corpus receipt/proof/key, accepted evaluation receipt/proof/key and
signed disjointness receipt/proof were submitted to the training-admission
validator under a temporary exact two-key trust map. The complete chain passes
with:

- status: `eligible-for-owner-training-effect-review`;
- corpus release SHA-256:
  `1f0e7d3777746e23472b0daa85dc7d103da0ac7ce09fe192e1c0f44dd0abe710`;
- recipe SHA-256:
  `419a42c166d08e92084178ac897d3f011dc565ca1474ae8a4fba8be68c9aa0e9`;
- signatures verified: true;
- declared roles distinct: true;
- intersection count: zero;
- training authorized: false;
- sealed-evaluation access: false;
- authority: not granted;
- automatic routing: off;
- deployment: false.

The temporary trust map was process-local only. The compiled `TRUSTED_KEYS`
registry remains empty until the owner decision below.

## Exact owner trust decision

Owner acceptance is requested for only these fixed role-to-key bindings:

- `independent-j2-corpus-custodian` →
  `47feec850ae4dc67443249edcbc5c134c767e293c6dcc4bbede5a31c2749574c`;
- `independent-j2-evaluation-custodian` →
  `46685b0ebd4e1bcf65bfae35df4858373b2f928fe3f81ab267bfa58cedfa9498`.

Acceptance authorizes only a source commit pinning those two fingerprints and a
real content-free replay of the admission validator. It can advance J2 only to
`eligible-for-owner-training-effect-review`. It does not authorize training,
a Lab Hours reservation, model execution, sealed-evaluation disclosure,
deployment, routing, tools, service changes or automatic promotion.

Rejection leaves the compiled registry empty and J2 training admission closed.
