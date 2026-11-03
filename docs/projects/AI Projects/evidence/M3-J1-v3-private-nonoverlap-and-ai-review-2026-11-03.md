# M3 J1 candidate-v3 private non-overlap and AI review — 2026-11-03

## Outcome

**PASS.** Candidate-v2 failed closed with exactly one normalized-text overlap
against calibration-v1 and zero against the other six exposed corpora. It wrote
no success receipt and did not read the sealed holdout. The private reviewer
revealed only the matching public synthetic case identifier,
`j1-train-label-07-case-04`; no private request text was printed or copied.

Candidate-v3 changes only that one public synthetic sentence while preserving
its identifier, split and coherent label. Historical v2 source and fixture are
unchanged. The new exact identities are:

- source/fixture SHA-256:
  `a625e6778b8c26fc99ae4336979e4be88dcf4662fe4f91dba7163cf7804277d5`;
- normalized-text-set SHA-256:
  `b0f466221d401e6464493afcd5b6c088f342de31b852387b8972014b3e2eb192`;
- ontology SHA-256:
  `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`;
- 400 unique cases, balanced 320/80 with 20/5 per each of 16 labels.

## Private gate

The purpose-built v3 reviewer ran directly against the documented
human-controlled `cases.json` artifacts. It returned `status=complete`,
`reference_count=7`, `receipts_written=7`, `sealed_holdout_read=false` and
`authority=not-granted`. Independent `validate_set` accepted all seven receipts
with no errors and one shared v3 subject identity. The retained content-free
private-review result SHA-256 is `4528634c…6356`; the seven receipt file hashes
are retained in the human-controlled private record.

## Independent AI release review

Three independent reviewers compared v2 and v3 and returned `PROMOTE`:

1. the revised request is a natural, clear public general-knowledge question;
2. `L-826ce72f3700` remains the exact `general-answer/public/facts.answer`
   coherent label;
3. interpreter compatibility is unchanged;
4. there is no personal, private, safety-sensitive, effectful or authority
   content; and
5. the other 399 rows are unchanged.

One reviewer found a stale v2 name in a v3 validation error; it was corrected
before freeze. The focused corpus, private-review, label-review and receipt
suite passes 29/29.

## Decision

Candidate-v3 is accepted as the corpus input for a **training-recipe release
candidate**. This is not model promotion. No training, public-gate access,
holdout access, threshold selection, routing or authority is granted. The next
work is to freeze a reproducible local training recipe, preprocessing/tokenizer
contract, label map, artifact manifest and deterministic guard boundary for
Jason's human promotion review.
