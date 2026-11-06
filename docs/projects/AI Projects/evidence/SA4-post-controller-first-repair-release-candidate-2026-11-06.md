# SA4 post-controller first-repair release candidate — 2026-11-06

Release v5 binds both validated inactive installations, all eight installed
transaction/controller source hashes, the unchanged drifted canary and the
same exact one-file repair plan. Its canonical packet digest is
`8b9ad5ce…beff`.

It requires fresh unique owner/AI-PAM authority, fresh installed-hash and
runtime checks, owner-created controls and the fixed observer bridge protocol.
Success permits one observer signature; rollback permits exactly two. Limits
remain one repair, at most one rollback, zero retry, no restart, routing off
and no automatic promotion. The packet grants no authority and invokes
nothing. Four focused tests and the complete 191-test SA4 suite pass.

The fresh unsigned authority builder uses unique grant ID
`sa4-canary-first-grant-v5-20261106`, rejects prior release drift, and creates
only 15-minute AI-PAM and 30-minute owner statements. It does not sign. The
expanded suite passes 194/194.
