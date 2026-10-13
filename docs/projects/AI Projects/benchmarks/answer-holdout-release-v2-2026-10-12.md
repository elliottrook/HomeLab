# Aster assistant-answer fictional holdout v2 — sealed release

**State:** Sealed and independently AI-reviewed offline on 2026-10-12. No
inference model has received v2; no route or tool promotion follows. V2 is a
new corpus because the v1 remote response was lost at a local evidence write.
The v1 questions must not be replayed as fresh evidence.

| Protected artifact | SHA-256 |
|---|---|
| Candidate-visible `cases.jsonl` | `8c5293382a457cbcf4f9999a8904820d6b1d126477fbfc6b672b41a87b62cab9` |
| Hidden `answer-key.jsonl` | `fef83e8223df3b3190cd3555e707aa80a24d0415e3b769099091cbbfe3a0edc3` |
| Custodian `manifest.json` | `5f0a8daa675a6a33d2d502b080ba0bf94f96551303aff3b45415344079683a59` |
| Separate AI review receipt | `fb96ebd94443c2f0b41cecab37e357d3c494c077dc41c779399ae4284c74bc3d` |

The private files are in
`~/Library/Application Support/Aster-Stream-A-Evidence/answer-holdout-20261012-v2/`
on the Mac Mini, directory mode 0700 and files mode 0600. Source copies are
under owner-only `/private/tmp`. All four copied hashes were verified;
`validate_answer_holdout.py` passed on the protected copy. Recoverable backup
remains **UNKNOWN**. No case, label or raw answer text is in Git.

There are 20 cases, two in each of ten assistant request families; expected
outcomes are ten useful answers, five justified abstentions and five correct
denials. Ten cases have specific private-context locality constraints and ten
have none. Maximum tool scope is `none` throughout. A fresh AI reviewer in
this same Codex window accepted 20/20, rejected zero, checked the frozen
sources, rubric and prohibited claims, and found no material overlap with the
six exposed development cases. A URL-shaped example uses the reserved
`.example` domain. This is AI review, **not human ground truth**.

The intended first candidate is the accepted local 9B reasoning-off service
under [profile v2](a1-answer-holdout-9b-profile-v2.json), SHA-256
`97ba9f9b68b0f294f52d76fb6f34cb05540d040dbc7698688b3e2879c2cf0402`.
Its run card remains BLOCKED until a new live lab/backup/service admission
check and safe reservation interval. The direct backend path does not measure
native Aster/Companion user-facing latency. Even a clean score is only
development evidence at two cases per class and does not authorize routing,
permissions or operational autonomy.
