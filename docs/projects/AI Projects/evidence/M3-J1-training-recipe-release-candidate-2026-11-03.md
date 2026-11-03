# M3 J1 training-recipe release candidate — 2026-11-03

## Recommendation

**PROMOTE FOR ONE BOUNDED TRAINING RUN after Jason's review.** This packet is
the review gate Jason requested; transient validation training retained no
model artifact and promoted nothing. No public or sealed evaluation data has
been opened.

## Candidate

The recipe is a compact 16-way fixed-alpha multinomial classifier trained from
scratch on the accepted J1 candidate-v3 corpus. It uses deterministic
NFKC/case-folded word, word-bigram and character 3–5-gram features mapped into
a fixed 4,096-dimension hash space. Alpha, label order and ten-decimal artifact
quantization are fixed. The portable dependency-free CPU implementation is the
only authoritative reference for this candidate.

The training partition is exactly 320 rows. The separate 80-row frozen
validation partition may select only a margin threshold from the fixed
0.000–1.000 grid, maximizing coverage subject to exact accepted predictions
and a preregistered floor of 48/80 accepted rows.
Public development/calibration inputs and the sealed holdout are forbidden to
the trainer. Network access, tools, routing and authority are also forbidden.

Exact source identities:

- recipe `e73590ca…8398`;
- recipe tests `8bc35c12…2baf`;
- corpus `a625e677…77d5`;
- ontology source `6e7ee332…948a`;
- deterministic guard `d7d62d19…7135`;
- content-free recipe-manifest output `de0c794b…3580`.

The release-candidate manifest binds all seven private non-overlap receipt
hashes and the successful private result, but contains no private text or path.
The training entry point now requires those exact bytes rather than accepting
schema-equivalent substitutes. It explicitly records `artifact.status=not-trained`,
authority not granted and automatic routing off.

The first linear recipe was rejected by three independent AI reviewers because
its real frozen path achieved only 60/80 and could not select a threshold. That
candidate was not promoted. The corrected learner's real exact-receipt path
achieves 70/80 overall and selects margin `0.375`, accepting 50/80 with 50/50
exact. It selects on already quantized weights, serializes a self-hashed
artifact, reloads it and proves the full 80-row prediction record unchanged.
Threshold selection evaluates the final guarded interpretation, not merely the
raw label. The runtime projection preserves an already coherent whole label
unless the guard makes its disposition strictly more restrictive, while always
retaining the deterministic personal-sensitivity floor. The artifact reader
requires the externally expected artifact digest and validates every frozen
decision field before inference.

## Required bounded run after promotion

1. Revalidate the exact corpus, seven receipt set, source hashes and absent
   artifact.
2. Train once in a network-isolated temporary directory using only the 320
   training rows.
3. Select the margin gate only from the 80 validation rows, requiring at least
   48 exact accepted rows.
4. Serialize and independently re-read the self-hashed artifact; reproduce it
   from a second clean CPU run before accepting determinism.
5. Freeze preprocessing, label map, weights, threshold and runtime manifest.
6. Only then expose the already frozen 24-case public gate once. Admission
   remains at least 23/24 exact, zero unsafe false routes and zero routed
   privacy underclassifications. Any failure rejects J1 without tuning or
   opening the holdout.

## Current proof and exclusions

The revised recipe/release tests pass 13/13 with the real private directory,
including an exact-byte seven-receipt run, guarded accepted-row equality,
privacy-preserving abstention and post-serialization replay. A retained
content-free validation result binds source `e73590ca…8398`, tests
`8bc35c12…2baf`, release candidate `81a4f40a…bbfb` and the unretained artifact
digest `606bd761…ae7c`; it contains no private text or path and explicitly says
that no artifact was retained. The v3 corpus has three independent AI
PROMOTE reviews and seven validated zero-overlap receipts. This packet does
not authorize training, a Lab Hours booking, public-gate access, holdout access,
deployment, model replacement, service restart, routing or tool authority.

Three fresh independent reviewers then rechecked the stable corrected tree and
all returned **PROMOTE**. They independently reproduced or verified 70/80 raw
and guarded exact, margin 0.375, 50/50 accepted exact, coherent-label
preservation, privacy-floor abstention, exact receipt/result binding, quantized
replay and external artifact-digest enforcement. The candidate is therefore
ready for Jason's human promotion review; it is not yet authorized to retain a
trained artifact.
