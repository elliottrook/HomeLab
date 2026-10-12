# SA3 sealed holdout run — 2026-10-12

Status: **quality gate failed; retain Qwen outside operational sysadmin use**.

Jason approved activation with four separate sub-agent custody roles. The
custodian authored 20 sanitized cases in private owner-only storage; the
reviewer accepted all 20, found five insufficient-evidence cases, found no
fixture overlap, and found no symlinks. The evaluator received the fixed
label-free bundle only after the review and release manifest were frozen. The
scorer received labels only after the result digest was sealed.

The sealed release digest is
`23609cbcc0ddd2b2eb12f22fad19f73e350654b9b5cab899f9b41cc484acdf33`.
Content-free artifact hashes are:

| Artifact | SHA-256 |
|---|---|
| Case bundle | `6ebb0910b3121be52d8149346d7a3dbe47d972985d2ac06ebf009c1149a43c46` |
| Release manifest | `d05d2f912ecf41be104f9c035763eae4d2741b27e6d5990501262241c332dcc8` |
| Evaluation results | `11918884e2e028fe1016b942829a582f5ed65dcee872c39d2aaf51e00e8be24e` |
| Score summary | `a88e78450f970d3ae4b3c29b1470b80e1a643e8c50a2c8e37a5804db5b5e703f` |

All 20 cases were sent through the tool-free baseline. Five cases completed;
15 failed the output contract before answer-quality dimensions could be
scored. All five insufficient-evidence cases completed as abstentions. No
prohibited effects or false-completion claims were observed. The required
gate was 18/20 actionable passes with at least 4/4 abstentions; actual
actionable passes were 0/15, so the gate failed.

The inference service returned healthy and idle. No production configuration,
tool authority, model settings, or deployment changed. This is single-operator
procedural evidence, not an external audit or a general reliability claim.
