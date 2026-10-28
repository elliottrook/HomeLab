# SA2 Forgejo registered-producer boundary — 2026-10-28

## Result

**SOURCE AND TARGET-PYTHON PASS; NOT DEPLOYED.** Stream A now has a fourth
fixed evidence source for the adaptive investigation catalogue:
`forgejo-main/git`. It reads only the existing sanitized Forgejo report at the
fixed Aster source-report path. It cannot open a Git remote, discover a target,
accept a path from the model, use credentials, run a subprocess or repair
anything.

## Model-visible evidence

The adapter emits only:

- repository, archived, open-issue and open-pull counts;
- failed and nonterminal latest-action counts;
- a 24-hex report digest;
- a bounded `ok`, `warn`, `fail` or `unavailable` state.

Repository owners/names, branches, commit identities, action timestamps,
report paths and source-validation details are never copied into incident
evidence. Tests explicitly assert that private fixture identities and commit
IDs do not survive aggregation.

## Validation

- Local focused suite: **44/44 PASS**.
- LXC104 Python 3.13 temporary packet: **44/44 PASS**.
- Corrected packet SHA-256:
  `b86c101d6daa3a05d995f539182ab551b4f7d83137bf5a2a18180bd7df2f8ecc`.
- Temporary packet and extraction directory were removed after the target run.

The first target packet omitted the pinned
`evals/sysadmin-producer-fixture.json`: 31 tests passed and 13 store tests
could not start. No candidate file was installed. The corrected packet added
the exact fixture and all 44 tests passed.

## Remaining release gate

The producer is now integrated into a separately tracked
[four-source adaptive candidate](SA1-SA3-forgejo-expanded-candidate-result-2026-10-28.md),
which passes 80/80 target tests and one complete isolated connected run. It is
still source-only. Deployment requires an exact manifest, current live-file
predecessor check, rollback-capable installer, independent exact-source review
and one separately approved Aster Agent restart. No automatic handover, repair
authority or generic Git access follows.
