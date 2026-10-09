# D3 Companion refresh and recovery replacement gate — 2026-10-09

**Status: local candidate; not installed.** The fixed twelve-question
experiment is complete. This gate is only for replacing the installed native
Companion with a build that removes a redundant Keychain read during token
refresh and can read completed turns that include internal reasoning items.
It does not authorize any new Codex question, tool, credential grant, policy
change, worker activation, or remote Git write.

## Evidence and exact change

The installed app stalled on the main thread inside
`AuthManager.refresh` → `SessionStorage.save` →
`KeychainStore.get("oidc_session_v2")` → `SecItemCopyMatching` after the
evaluation. The current `save` writes the new token set and immediately reads
it back. The local candidate uses `SecItemUpdate`/`SecItemAdd` success as the
write result and removes only that extra read. A failed write still reports a
nonpersistent session. Startup still reads the saved login, and a changed
ad-hoc app signature can still trigger a macOS Keychain prompt; this change
must not be described as universal prompt elimination.

Five of twelve completed turns contained an internal `reasoning` item. The
installed recovery helper rejected those turns because it allowed only user
and final-agent items. The candidate allows `reasoning` as an inert item,
still rejects tool items, and returns only one exact final answer from an
owner-bound completed turn. Read-only replay of all twelve historical turns
with the candidate succeeded without starting inference or printing answers.

Candidate source and test evidence: six focused Python bridge tests and 49
native Companion tests passed; strict code-signature verification passed. The
uninstalled candidate executable SHA-256 is
`2a1ec983b2701b614ffeecf0f8f1bd2de33005e51a5431ec8de9cd704c1aa4a6`.
Its bundled send preflight manifest SHA-256 is
`34d349045dea8ae8410ccc984e508f1754348539f0491fe542e0bd31f78b3753`.
The currently installed executable SHA-256 is
`814a0fd4e01d3179e9b5cf6c0208f428895ea7798c905b55508b88146da0a075`.

## Bounded release procedure if approved

1. Ensure the existing Companion Keychain dialog, if any, has been resolved;
   do not enter, display or copy token material. Close Companion cleanly.
2. Make a fresh owner-local rollback copy of the installed app and confirm its
   executable hash. Preserve the existing
   `/Applications/AsterCompanion.pre-D3-recovery-20261009.app` rollback too.
3. Replace only `/Applications/AsterCompanion.app` with the signed candidate;
   verify the installed executable hash and strict code signature.
4. Open normal mode first. Check signed-in Aster composer, AI-PAM approvals
   view, and closed ordinary Codex requests. Do not send an Aster or Codex
   question as part of this smoke check.
5. Run the installed bundled helper's read-only recovery against the twelve
   exact completed request IDs, reporting only counts and safety flags. No
   prompt or answer text enters logs. Verify no new submission event or turn.
6. Observe normal token refresh and at least one app restart for repeat
   Keychain prompts. If a prompt recurs, record only app/key names and do not
   widen access for `/usr/bin/security` or the worker credential. A refresh
   observation may need to wait for natural token expiry; do not alter system
   clock or credentials to force it.

Rollback: if normal Companion or AI-PAM regresses, close the candidate and
restore the fresh rollback app at the original path, verify its recorded hash,
and leave the new release closed. Do not delete either rollback until a later
review. A second ad-hoc signature may itself prompt for Companion's saved
login on restoration.

This replacement is a reliability repair, not D3 graduation. Independent
answer review, crash/sleep/wake reconciliation, and a separate routine-use
decision remain open even if the app replacement validates successfully.

## Installation checkpoint — 2026-10-09

Jason approved this exact replacement. Companion closed cleanly after the
finite-set completion screen. The former installed app was copied to
`/private/tmp/AsterCompanion.pre-D3-refresh-20261009.app` and moved to
`/Applications/AsterCompanion.pre-D3-refresh-20261009.app`; its executable
hash is the recorded old hash above. The candidate was installed at
`/Applications/AsterCompanion.app`; its executable matches the candidate hash
above and strict code-signature verification passes. No new model request or
remote Git write occurred during replacement.

At first normal launch, the UI has not yet opened. A local process sample shows
the app waiting in `AuthManager.init` → `KeychainStore.get` →
`SecItemCopyMatching` for its existing saved-login item, as expected after an
ad-hoc signed app replacement. Jason must resolve the macOS prompt before the
normal-screen and read-only recovery release checks can be completed. The
refresh read-back fix has not yet been validated in live operation. Do not
count installation hash/signature verification as a functional pass.
