# M4 independent acceptance boundary — 2026-10-26

## Result

**SOURCE PASS / HUMAN DECISION AND CUSTODY STILL OPEN.** The remaining M4 trust
gate is now machine-checkable without letting the experiment writer manufacture
the decision. `m4_independent_acceptance.py` validates a separately supplied
human record against the exact 164-event artifact and ledger head.

The follow-on lineage correction also requires the exact reviewed candidate
commit `af2cc4f988ca9ed1a69e0d425c2bb7991ffa7f71`. The initial validator accepted
any syntactically valid 40-character commit, which could bind the correct
artifact and ledger to an unrelated revision. That shape-only check is now
closed and covered by a negative test.

The record must name a reviewer, an accepted commit, retain/reject/request-more-
evidence, a UTC review time, explicit limits and one independently controlled
custody method. It stores only a digest of the custody reference. It fixes the
scope to synthetic-only, rejects private collection and always reports
`authority: not-granted`. Duplicate keys, repository-only custody, changed
artifact identity, non-UTC time and any self-grant fail closed.

Three focused tests and the combined 34-test M4 evidence/reconstruction suite
pass in the pinned Python 3.12.14/Pydantic 2.14.1 environment. This validator
does not prove that the reviewer or
external record exists; it deliberately cannot create the acceptance record.
Jason still needs to review the synthetic-only design and retain the exact
commit/artifact/head in a location the experiment writer cannot replace. A
future real-data proposal still needs numeric retention, consent, access,
backup and deletion rules; none are inherited from this checkpoint.
