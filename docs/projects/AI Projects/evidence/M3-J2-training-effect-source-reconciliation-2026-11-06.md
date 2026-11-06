# M3 J2 training-effect source reconciliation — 2026-11-06

## Outcome

The first post-admission source review found and corrected two deterministic
post-training rejection defects before any training effect.

First, the artifact contract still pinned the superseded recipe digest
`aba6e3d7…23ec`, while the frozen admitted recipe is
`419a42c1…c9aa0e9`. A legitimate artifact produced from the admitted recipe
would therefore have failed validation after the full training cost. The
artifact contract now pins the exact frozen recipe file, and a regression
recomputes that fixture digest.

Second, the accepted corpus uses validation case IDs `case-48` through
`case-59` for each of sixteen labels, but the replay contract required
`case-00` through `case-11`. The replay contract and fixtures now require the
already accepted 192-case identity set without changing corpus bytes. A
content-free real-corpus check builds the validation-truth envelope and passes
the corrected replay identity contract at 192 rows, SHA-256
`cfb58d9bb29667a762b01c246f3e52e0d5a9d29158aab21f22831bde573c2eab`.

The complete J2 source suite passes 110/110. No corpus, receipt, key or sealed
evaluation identity changed.

## Remaining training-effect boundary

Training is not yet approval-ready. The repository has frozen primitives,
forward/backward math, batch updates, validation selection, artifact validation
and replay validation, but no end-to-end owner that composes:

1. exact admitted input loading and the 768/192 split;
2. forty complete single-thread CPU epochs and after-each-epoch checkpoints;
3. validation summaries, selected checkpoint and threshold receipt;
4. ten-decimal artifact emission with exact admission/release bindings;
5. two clean CPU replay records and final replay validation;
6. create-only output custody, bounded failure evidence and cleanup/retention.

The next autonomous work is that source-only transaction owner plus disposable
tests. A later effect review must also choose the execution host, prove resource
headroom, and determine whether the selected host/workload needs a Lab Hours
reservation in addition to any lease/operation lock. This record creates no
booking and authorizes no training, service impact, sealed-evaluation access,
deployment or routing.
