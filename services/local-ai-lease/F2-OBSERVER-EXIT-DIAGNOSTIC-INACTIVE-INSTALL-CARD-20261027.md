# F2 observer-exit diagnostic — inactive installation card

Status: **SOURCE TESTED; HOST CHANGE NOT AUTHORIZED**

The October 27 exact cycle preserved only `OBSERVER_EXIT_NONZERO` after the
observer child returned a bounded failure projection. The coordinator checked
the child's exit status before parsing that content-free projection, so it
discarded the already available `preflight`, `observer` or `result` phase.
This one-file correction retains that bounded phase without retaining command
output, archive contents, paths or exception text.

## Frozen candidate

| Item | SHA-256 |
|---|---|
| Installed predecessor `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193` |
| Candidate `scripts/local-ai/f2_scheduled_release_candidate.py` | `efe8bc99efd95ce85d2dbe3c8218419fdb187ceaa065cf59a906e7c0323987ec` |
| Focused test `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `40b1d2a25620fad70c6018f1092cf68f48061bcaee58465225f2d425e3863d7d` |
| Historical-pin test `scripts/local-ai/test_f2_mirror_deferred_card.py` | `1c7dc66a9f040a7d070a7749ef490f1c3270ba5a0d0864bf9d3ff08ec23610f3` |

The coordinator accepts only a child JSON object containing exactly
`state=no_go`, a bounded identifier-shaped `error_class`, and one of three
known phases. It maps those phases to
`OBSERVER_CHILD_PREFLIGHT_DENIED`, `OBSERVER_CHILD_SCAN_FAILED` or
`OBSERVER_CHILD_RESULT_INVALID`. Oversized, malformed, extra-field or unknown
output retains the conservative `OBSERVER_EXIT_NONZERO` class.

Focused coordinator and observer tests pass 31/31. The complete F2 suite passes
55 tests with one expected non-root custody skip. Historical cards remain
immutable: their tests now validate their frozen pins instead of requiring an
old card to match the moving source tree.

## Bounded inactive installation

After separate approval, the platform owner may:

1. require the installed predecessor hash and root-owned one-link mode `0644`;
2. preserve that exact file in a new root-only rollback directory;
3. copy only the candidate coordinator to the installed path as root-owned,
   one-link mode `0644`;
4. verify the installed candidate hash; and
5. run the focused and broader F2 tests on target Linux using a clean source
   packet.

Any predecessor, custody, hash, import or test mismatch must restore the saved
file and stop. Leave all recurring and exact-date F2 timers disabled and
inactive. Verify the preserved October 27 state digest is unchanged and that
no F2/`zstd` child, lease, lock or receipt exists after installation.

This card authorizes no host change by itself. It does not authorize a timer,
F2 scan, retry, F3 conversion, receipt, lease, service stop, model call,
schedule change or Git push. A future exact-cycle activation requires a fresh
date-specific card, independent review and separate approval.
