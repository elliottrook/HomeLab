# D4 candidate-g fresh booking v2 review — 2026-11-04

## Decision

**STATIC GO; EXACT RESTART DECISION PENDING.**

The proposed 12:30–14:00 host-local window is clear in the authoritative
ledger. Card v2 adds the missing complete installed-manifest verification to
static admission: all 34 pins pass on the installed runner, including both EPUB
correction files and corrected manifest `4d8e7db2…2b92`. Target tests pass
22/22, the lease and shared-state boundary are clean, and the failed 09:30
booking remains terminal.

This is a fresh booking, not a retry. It still crosses the retained production
service stop/start boundary and therefore awaits that one exact decision.
Runtime gates remain volatile and fail closed. No model change, second attempt,
extension, deployment, routing promotion or tool authority is included.
