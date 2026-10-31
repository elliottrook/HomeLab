# M3 J1 v2 release candidate and private-review handoff — 2026-10-31

## Outcome

The Cartesian v1 corpus is superseded. The exact v2 candidate contains 400
individually written synthetic requests and has passed three independent AI
release reviews after two correction rounds. It is ready for the seven-corpus
private non-overlap gate. It is not yet a training release and grants no model,
routing, threshold or tool authority.

## Exact candidate

- fixture: `scripts/aster-adaptive/fixtures/nlu-j1-training-draft-v2.json`
- source SHA-256: `a70461c037ef24bf7a346dcefa769d8de938d6c54ddd8acf7d58c1e1370e7b79`
- normalized-text-set SHA-256: `891d7dc46c1567f3f7a1e5b489b9e043044944ae843f6b41b6b2cebd964192a3`
- ontology SHA-256: `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`
- balance: 320 train / 80 validation; 20/5 for each of 16 labels
- public `development-v1` overlap: zero
- unique normalized requests: 400
- unique four-token openings: at least 390; maximum reuse: 4
- actual interpreter drift: zero across all 400 rows

The deterministic quality boundary rejects the old v1 draft and accepts this
candidate. It checks request uniqueness, plausible length, four-token opening
diversity, exact balance, public disjointness and byte-for-byte reproduction
from the source generator.

## Independent AI review

Three independent reviewers inspected all 400 text/label pairs in each round.
The first candidate was rejected for ontology/runtime conflicts, physical
access-control examples, artificial wording and a lexical shortcut across the
unsupported classes. The second was rejected for residual prose defects,
forecast ambiguity and validation examples too close to training phrases.

The exact candidate above received three final `PROMOTE` verdicts:

- reviewer 1: no remaining defects;
- reviewer 2: 400/400 inspected, zero semantic mislabels, interpreter drifts,
  safety/privacy underclassifications, language defects or blockers;
- reviewer 3: 400/400 inspected, zero text or label revisions required.

These are AI quality reviews, not Jason's final promotion decision.

## Private-corpus gate

The exact-source reviewer is
`scripts/aster-adaptive/nlu_joint_training_private_review_v2.py`. Run it only
on the human-controlled machine holding the private corpora:

```console
cd scripts/aster-adaptive
python3 -B nlu_joint_training_private_review_v2.py \
  --subject fixtures/nlu-j1-training-draft-v2.json \
  --development-v1 /human-controlled/development-v1.json \
  --calibration-v1 /human-controlled/calibration-v1.json \
  --calibration-v2 /human-controlled/calibration-v2.json \
  --calibration-v3 /human-controlled/calibration-v3.json \
  --calibration-v4 /human-controlled/calibration-v4.json \
  --calibration-v5 /human-controlled/calibration-v5.json \
  --calibration-v6 /human-controlled/calibration-v6.json \
  --output-dir /human-controlled/j1-v2-private-review-20261031
```

The command emits no request text. It writes seven content-free receipts only
when every pinned corpus matches and every overlap count is zero. Any missing,
extra, changed or overlapping corpus is NO-GO with no partial success receipt.
The sealed holdout is neither accepted nor read.

## Remaining gate

Jason should receive the human review packet only after the seven exact private
receipts pass. If they pass, freeze a training recipe and artifact manifest for
Jason's promotion review. If they fail, retain the content-free result, revise
the synthetic subject without inspecting or copying private text, and repeat
all source, semantic and non-overlap gates on the new identity.
