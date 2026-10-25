# M3 NLU calibration source-packet validation — 2026-10-25

> Result: **PASS — SOURCE PACKET VERIFIED; NO STAGING EFFECT**

The pinned staging validator at source commit
`531c07fc02d77b36f0f27b9166f9e1b6c831681e` was run against the actual ten
source inputs named by the frozen LXC110 staging manifest. The private
synthetic cases remained in owner-only Mac custody. No file was copied, opened
for writing or printed.

| Check | Result |
|---|---|
| staging manifest SHA-256 | `be1e554367cba081135db12723a0b54eb6dabfe92b2576d41423a354e4988463` |
| declared inputs | 10 |
| byte-verified inputs | 10 |
| verified aggregate bytes | 92,467 |
| exact name set | pass |
| regular files with no symlink following | pass |
| per-file SHA-256 against frozen manifest | pass |
| authority | `not-granted` |

This closes the source-packet byte-readiness check only. LXC staging, lease
acquisition, model requests, scoring, threshold selection, holdout access,
shadowing and automatic routing remain unperformed and unauthorized by this
evidence.

