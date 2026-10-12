# Aster assistant-answer fictional holdout v1 — custody record

**State:** Sealed offline development corpus, 2026-10-12; no model invocation
or promotion. Scope is assistant answers, not the B60 project's SA3 sysadmin
corpus. All content is fictional and synthetic. This page is intentionally
content-free.

| Private artifact | SHA-256 |
|---|---|
| Candidate-visible cases (20) | `4b9ca94714414248d3f429237f7385f27ddd132d4f6825676349b85cb5ccc7ae` |
| Hidden answer key | `27b6049546abcda89a0c725fffad3452fc6a58ce2595e87a73560545a0933744` |
| Custodian manifest | `0e36b6ec38cae455e899e0b6b4a7490361af98f4189f2699493f248a916ffe86` |
| Separate AI review receipt | `0d45d5c0cae80071f5ae933155d178a7d1b5950ee179d7ec820f459ff6018b11` |
| Separate AI review summary | `f4dfc4853c2670c8a4084980d0ed4e2baa026495c5e1f6ac49c2a19c6466aef4` |
| Development-fixture non-overlap addendum | `9a91c2308a389c9b834a61101151011a299821cc9641939e8ecfd94b44c0755c` |

The private files are in
`~/Library/Application Support/Aster-Stream-A-Evidence/answer-holdout-20261012-v1/`
on the Mac Mini, owner-only. Their source copies are ephemeral `/private/tmp`
artifacts. `scripts/aster-adaptive/validate_answer_holdout.py` returned exact
case/key alignment and manifest agreement after the copy. The source and
protected copies have the same listed hashes. No case, label or response text
is in Git. The local folder's backup/recovery path is **UNKNOWN** and must not
be presumed from this record.

Reviewer separation was limited to fresh Codex sub-agents in the same window.
The 20/20 acceptance and 0/120 material overlap checks are useful privacy
and contamination checks, but they are not independent human ground truth.
The two cases per family are too few for stable per-class rates or p95 latency.

Before a run, freeze the exact model/runtime/prompt, token and timeout budget,
case order/seed, maximum tool scope `none`, scorer source revision and
adjudication role. Recheck service occupancy and any whole-host lease live.
Seal raw responses before the answer key is opened. A later correction to
cases or labels requires v2 and cannot be silently substituted.
