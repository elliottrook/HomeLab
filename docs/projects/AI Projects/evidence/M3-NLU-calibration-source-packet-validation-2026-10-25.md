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

## Repinned packet after response-envelope correction

The bounded llama response-envelope compatibility correction changed only the
runner and its manifest pin. The actual source packet was revalidated against
manifest SHA-256 `357b4e3d5514fe32b1509ac27f9eac3940edb0635db3a5008b4f29fc4f124a00`:
10/10 inputs and 93,612 aggregate bytes passed. The original measurement above
is retained as superseded provenance; the repinned measurement is the current
staging input.

## Dependency-closure correction

The first inactive staging attempt proved that the ten-file packet omitted
`nlu_candidate_bundle.py`, which `nlu_calibration_release.py` imports. The
attempt stopped before its atomic rename and removed the new LXC directory.
The source manifest now pins that missing module at SHA-256
`5a797b2f0166d6ead276c0487887074ea1f78396d2ddfcd4ea7d6915df36e156`.
The corrected manifest SHA-256 is
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
All 11 inputs, 98,414 aggregate bytes, passed the exact byte validator and all
eight Python modules imported with bytecode writes disabled. This corrected
packet supersedes the ten-file packet for any later LXC staging.

