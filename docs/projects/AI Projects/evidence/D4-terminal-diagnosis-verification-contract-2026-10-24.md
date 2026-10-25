# D4 terminal diagnosis and verification contract — 2026-10-24

## Trigger

The independent model-blind review of development attempt 4 passed evidence,
freshness, scope and no-false-completion for all twelve answers, but passed
diagnosis for only eight and verification for none. The private review showed
two answer-contract gaps that can be corrected without another model call:
terminal answers did not have to state the distinction they resolved, and
verification was unstructured prose rather than a required bounded postcheck.

## Offline correction

The synthetic investigation response contract now requires two additional
terminal elements:

- `discrimination` states the bounded distinction resolved by current evidence;
  a clarification must identify the missing allowed observation and the
  alternatives it would distinguish.
- `verification` contains a bounded check, expected condition, preserved
  boundary and literal `performed: false`.

Check-selection responses must leave these terminal fields empty. Conclude and
clarify responses must populate them. The validator rejects missing or extra
fields, empty terminal verification, nonempty premature terminal claims,
`performed: true`, oversized or mistyped values, and first-person claims that
the model ran, changed, restarted, fixed or verified something. The durable
journal independently revalidates the same answer shape before retaining it.
No authority, capability, effect or connected tool was added.

## Evidence

- `sa3_investigation.py` SHA-256:
  `3f3a081367c0d1674e6c6ea258bf6319bb3dde002a2a2f2608fad6c780c68ef0`
- `sa3_fresh_package.py` SHA-256:
  `5015ad8e212cd7fe22d556a0e50242b225e5da372d5b32b8585404f2decc8bfd`
- Focused contract, package, packet and executor tests: 45/45 passed.
- Complete evaluation suite after packet and decision-rule hardening: 161/161
  passed.

The tests use synthetic answers and do not call a model, open the private
holdout, connect a tool or alter production.

## Decision and next gate

The correction closes the known offline answer-shape gap but does not repair or
reinterpret attempt 4. A new development attempt would use a different run
digest because the implementation hashes changed. Before any model call,
freeze that digest and a predeclared development decision rule. Those artifacts
are now frozen separately for candidate-B; the new run still needs explicit
approval and another fresh model-blind review. A connected read-only pilot
remains **NO-GO** until that evidence exists.
