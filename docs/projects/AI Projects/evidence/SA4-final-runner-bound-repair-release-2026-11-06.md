# SA4 final runner-bound repair release — 2026-11-06

Release v6 binds all three inactive installation results, nine exact installed
sources, the final-path no-argument preflight, unchanged drifted canary and one
fixed repair plan. Canonical packet digest is `77466737…869a`.

It requires new unique owner/AI-PAM authority and fresh runtime/hash/production
gates. The fixed runner owns ledger initialization, bounded epochs and terminal
or uncertain evidence; the controller/bridge owns one success or two rollback
observer signatures. Limits remain one repair, at most one rollback, zero
retry, no restart, routing off and no promotion. It grants no authority.

Three focused release tests pass. The fresh unsigned authority builder uses
unique grant ID `sa4-canary-first-grant-v6-20261106`, rejects release drift and
creates only 15/30-minute grant/owner statements without signing. The complete
suite passes 210/210. Offline preparation is exhausted before exact approval.
