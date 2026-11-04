# M3 J2 custody-receipt boundary — 2026-11-04

## Decision

**SOURCE READY; NO CORPUS, EVALUATION OR TRAINING AUTHORIZED.**

The content-free receipt validator implements the next J2 offline milestone.
It requires three distinct identities: a corpus custodian, a label reviewer and
an evaluation custodian. It binds every receipt to preregistration manifest
`2abcd023…97ee` and rejects self-review or role reuse.

The corpus receipt requires 768 training and 192 validation rows, 16 labels,
zero normalized overlap against at least eight bound references, three exact
content digests and no text in the receipt. The evaluation receipt requires a
new sealed 32-case, 16-label, two-per-label boundary with trainer access
forbidden and no text in the receipt. The corpus and evaluation normalized
text-set digests must differ.

The combined admission is diagnostic only: it explicitly records
`training_authorized=false`, authority not granted and automatic routing off.
Seven focused tests pass for the valid shape and fail closed on counts, overlap,
content leakage, custody collapse, preregistration drift, seal/trainer-access
drift, self-hash drift and duplicate keys.

Next is independent creation of the three receipts and their underlying data;
the trainer must not see the evaluation content. This milestone does not
authorize generation, training, booking, model/backend change, service stop,
deployment, routing or tools.
