# M3 J2 preregistration boundary — 2026-11-04

## Decision

**SOURCE-ONLY J2 BOUNDARY FROZEN; NO CORPUS OR EVALUATION CREATED.**

J1 is closed at its failed public gate. J2 is deliberately not a repair of its
five exposed cases. It changes both representation and training family to a
small byte-level convolutional joint-label classifier trained from scratch,
with no pretrained weights or network access.

The manifest freezes a 512-byte input, 32-dimensional byte embeddings, three
convolution widths (3/5/7), 48 channels per width, global pooling, a
96-dimensional hidden layer and the existing 16 coherent joint labels. The
deterministic guard remains outside the learner and continues to own safety,
privacy floors and the non-authorizing envelope.

## Untouched-data contract

- a distinct custodian must create 768 training and 192 validation rows,
  balanced 48/12 per label;
- a distinct reviewer must accept every label;
- normalized overlap must be zero against every exposed corpus and the entire
  J1 corpus;
- a third custodian must create and seal a new 32-case evaluation boundary
  before training, with two cases per label and no trainer access;
- the existing sealed holdout remains unopened;
- J1's result, failures, artifact and weights are forbidden from training,
  selection and manifest inputs.

The future one-attempt evaluation bar is 31/32 exact, zero unsafe false routes
and zero routed privacy underclassification. Failure closes J2 without retry
or tuning on exposed cases.

## Proof and next work

The source validator and seven-test suite fail closed on architecture, corpus,
custodian, sealing, retry, runtime-effect and J1-identity drift. The next
offline milestone is the independent corpus/evaluation custody protocol and
content-free receipt schema. This boundary authorizes no corpus generation,
training, model/backend change, booking, service stop, deployment, routing or
tool authority.
