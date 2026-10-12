# D3 content-free session-refresh observation candidate — 2026-10-11

**Status: local source and test candidate only. The installed Companion remains
version 15 in ordinary mode. Routine manual Codex release remains HOLD.**

## Question and boundary

The earlier signed-in, prompt-free Companion request proved that an authenticated
path worked, but could not distinguish use of an unexpired access token from a
refresh-token exchange. Reading token values or forcing another Codex question
would not be justified by this gap. The next *ordinary-use* build can instead
emit a fixed event when `AuthManager` actually takes the refresh branch.

`AuthManager` now logs only one of seven fixed codes in the macOS unified log
under subsystem `com.elliottrook.aster-companion`, category `session`:
`refresh_started`, `refresh_succeeded_persisted`,
`refresh_succeeded_volatile`, `refresh_invalid_grant`,
`refresh_unavailable`, `refresh_cancelled`, or
`refresh_missing_credential`. No token, username, subject, request body,
expiry, Keychain item contents, prompt text, or answer is interpolated. The
event observer is injectable in tests; normal app behavior uses the fixed-code
logger. The established auth and Keychain paths otherwise remain unchanged.

## Verification and falsifiable gate

The 14 focused auth tests assert that two simultaneous requests yield one
refresh attempt and one persisted-success event; a failed Keychain save yields
the volatile result; temporary issuer failure and invalid grant remain distinct;
and a valid unexpired session emits no refresh event. The entire local native
suite passed: 57 tests, zero failures. No app was installed, registered,
launched or sent a model request as part of this change.

When a future native build is otherwise warranted and separately reviewed,
observe an ordinary authenticated read-only request after the app naturally
needs renewal. A `refresh_started` followed by
`refresh_succeeded_persisted`, no Keychain prompt, and successful request
would establish that the refresh path ran and its Keychain save reported
success. A later normal restart with prompt-free authenticated use would add
durability evidence. An absent event remains **unknown**; `volatile`,
`invalid_grant`, a prompt, or a failed authenticated request keeps the release
on HOLD. Log timestamps can establish ordering, not token lifetime or passkey
assurance. Neither a log line nor a signed-in UI alone proves sustained
reliability.

Do not ship a separate app update solely for this observation: the current
locally signed builds have prompted for Keychain access on update. Batch the
candidate with a justified, reviewed native release. Do not enable manual
Codex, connected tools, routing or AI-PAM Stage2 based on these offline tests.
The rollback is simply to omit this unused source candidate; any installed
native release still needs its own known-good copy, signature check and
authenticated rollback review.
