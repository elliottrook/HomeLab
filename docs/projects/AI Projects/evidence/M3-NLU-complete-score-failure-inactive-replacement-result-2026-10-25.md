# M3 NLU complete-score failure inactive replacement result — 2026-10-25

> Result: PASS — installed inactive; no calibration or model request

After three fail-closed transaction corrections, Jason approved the final
two-file inactive replacement at source commit `5fc31a17`. The transaction
completed at 23:52 PDT on October 25 (06:52 UTC October 26).

## Installed result

- scorer SHA-256:
  `7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd`;
- journal validator SHA-256:
  `966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb`;
- both files: root:root, mode `0600`, one-link regular files;
- packet validation: 11/11 files, 99,805 bytes, manifest SHA-256
  `7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80`;
- target-Linux scorer regressions: 9/9 passed; and
- installed runner/scorer/journal imports passed without bytecode writes.

Rollback checkpoint:
`/var/lib/aster-nlu-calibration/checkpoints/score-boundary-9f4da72d-20261026T065157Z`.
It retains the preceding scorer and journal hashes under root-only custody.

## Independent postcheck

The staged directory still contains exactly eleven files. `run.json`,
`attempt-journal.jsonl`, `__pycache__`, the temporary test root and an NLU
runner process are absent. The whole-host lease is `ready`; accepted llama is
active/running with zero restarts. The October 26 F2 preparation and final
timers remain enabled and active for 01:15 and 01:20 PDT. Exact transport and
installer files were removed.

No model call, calibration, score artifact, threshold selection, service stop,
lease, F2 change, route, deployment or Git push occurred. This closes the
inactive M3 packet consistency gate only. Fresh F2–F6 evidence and the serial
candidate-H outcome still precede the one approved-live calibration decision.
