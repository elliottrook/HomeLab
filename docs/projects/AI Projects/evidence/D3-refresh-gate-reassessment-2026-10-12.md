# D3 natural-refresh gate reassessment — 2026-10-12

**Decision: do not hold Stream A or the bounded, hidden Mac manual-Codex pilot
for another indefinite natural-refresh observation.** Continue automatic
routing and authority-boundary work independently. Do not claim appliance-grade
session reliability or routine manual-Codex release from this decision.

## Evidence

- The historical signed v16 executable produced nine `refresh_started` /
  `refresh_succeeded_persisted` pairs under ordinary aging. That is real
  evidence for v16, not proof about the installed composite.
- The installed composite `eb69280` kept `AuthManager.swift`, `KeychainStore`
  behavior and the existing auth tests unchanged from the pinned, previously
  accepted Companion source `f26e3c48`. Its stable signing requirement matches
  the preceding app. This avoids introducing the older v16 auth file or a new
  Keychain item during integration.
- On the exact installed composite, signed-in normal UI, fresh passkey
  verification, read-only OpenBao status, AI-PAM panel access, and one ordinary
  Aster response passed. The prior signed app is preserved in two verified
  local copies. No manual Codex question or infrastructure tool was used.
- Focused `swift test --filter AuthManagerTests` on the composite source passed
  9/9 on 2026-10-12. The tests cover one refresh for concurrent requests,
  rotated-token persistence, failure to save, revoked refresh, temporary
  failure, and session restoration. These are synthetic tests, not a live
  renewal of this installed process.

## Why the gate changes

The remaining risk is a recoverable session or Keychain interruption, not an
increase in authority: the manual pilot is hidden in ordinary mode, requires
reviewed cloud consent, and has no infrastructure tool grants. Requiring an
unbounded wait before continuing unrelated Stream A work has low information
value. The current Companion auth source also lacks v16's fixed-code
`refresh_started` instrumentation, so mere continued sign-in would not prove
the exact refresh path. A weak observation should not be treated as a strong
release gate simply because time passed.

This does **not** transfer the v16 result to the composite or excuse a known
failure. Keep the following bounded checks:

1. Continue normal use without forcing expiry, signing out, reading tokens or
   creating repeated model turns. Observe whether a later ordinary request
   succeeds after natural aging and whether a Keychain prompt recurs.
2. If a normal request fails with a session error or prompts repeatedly, hold
   the pilot, inspect only content-free status, and use the verified prior app
   if normal use is impaired. Diagnose before another install.
3. Before calling the manual Codex feature a routine user-facing release,
   verify the flagged UI and its explicit consent on the installed composite
   without sending an unnecessary new Codex question. This is a separate,
   finite feature check.
4. If future claims require measured refresh success rates, add safe event
   instrumentation in a separately reviewed update and measure over real
   sessions. Do not infer a rate from one token cycle or synthetic tests.

**Boundary:** this decision permits continued Stream A development and a
bounded local pilot; it grants no automatic route, connected tool, AI-PAM
permission or self-promotion. The next proof needed for automatic handover is
routing quality/calibration and policy conformance, not another passive wait
for this Mac session.
