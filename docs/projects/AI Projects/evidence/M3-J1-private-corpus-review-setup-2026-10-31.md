# M3 J1 private-corpus review setup — 2026-10-31

## Outcome

The J1 private-corpus review is ready for Jason or another human-controlled
custodian to run on the machine that holds the seven exposed corpora. The
review compares the exact 400-row synthetic draft with `development-v1` and
`calibration-v1` through `calibration-v6`. It writes only content-free results
and zero-overlap receipts.

This setup does not read or request the sealed holdout, train a model, choose a
threshold, enable routing or grant authority.

## Frozen subject

- source: `scripts/aster-adaptive/fixtures/nlu-j1-training-draft-v1.json`
- source SHA-256: `b736f0a94125e3b05238d9a54d2d6bdf107005f047c4b120cc43cbf1bf8fcefa`
- normalized-text-set SHA-256: `4cd89f296e1c2c5bd5484a6978f9de59b28f8befd407e84405a9e9a9339c1b6e`
- cases: 400

The seven expected reference identities and counts remain pinned in
`nlu_joint_training_nonoverlap_receipt_v1.py`. A missing reference, extra
reference, changed byte digest, changed normalized-set digest, duplicate text,
overlap or attempt to include the sealed holdout fails closed.

## Human-controlled run

Run this command only where the private corpus files already reside. Replace
the placeholder paths locally; do not commit the paths or copy the private
files into this repository.

```console
cd scripts/aster-adaptive
python3 -B nlu_joint_training_private_review_v1.py \
  --subject fixtures/nlu-j1-training-draft-v1.json \
  --development-v1 /human-controlled/development-v1.json \
  --calibration-v1 /human-controlled/calibration-v1.json \
  --calibration-v2 /human-controlled/calibration-v2.json \
  --calibration-v3 /human-controlled/calibration-v3.json \
  --calibration-v4 /human-controlled/calibration-v4.json \
  --calibration-v5 /human-controlled/calibration-v5.json \
  --calibration-v6 /human-controlled/calibration-v6.json \
  --output-dir /human-controlled/j1-private-review-20261031
```

The output directory must not already exist. It is created mode `0700`; each
result is created mode `0600` without following links. On complete success it
contains seven named receipt files and `private-review-result.json`. On a
measured overlap it contains only the content-free result, returns exit 2 and
writes no success receipt. Identity or schema drift aborts before output.

## Acceptance and next gate

Accept this gate only when:

1. the result says `status=complete`, `reference_count=7`,
   `receipts_written=7` and `sealed_holdout_read=false`;
2. `nlu_joint_training_nonoverlap_receipt_v1.validate_set` accepts the exact
   seven receipts; and
3. the existing independent label review remains source-bound.

The independent AI consensus accepted all 400 assigned labels, but all three
reviewers noted templated or unnatural wording. Therefore these receipts alone
do not release training. Jason's phrase-quality decision, or a corrected and
newly frozen synthetic draft, remains required before a training recipe and
artifact manifest can be frozen.

## Validation

The setup's focused tests cover successful content-free receipt production,
overlap NO-GO without partial success receipts, exact subject binding, changed
reference pins, missing/extra corpora and sealed-holdout rejection.
