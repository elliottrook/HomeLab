# D3 Companion composite: offline candidate, not a release

**Status: local candidate `eb69280` on `codex/aster-companion-composite`; no
installation, remote push or Codex question.** This candidate responds to
Jason's requirement that the native OpenBao seal/unseal controls survive the
manual Codex integration. The current installed app remains untouched.

The Companion app owner identified published source
`f26e3c4845cc49e11fa00a16881e17604e7ac266` as the current app baseline,
reported no further unpublished Companion edits in that line, and confirmed
that Jason accepted native sign-in and OpenBao recovery after its installation.
Stream A independently observed the installed executable SHA-256
`7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
The source-to-binary relation is an owner assertion, not a reproducible
binary-build proof. The owner reports no separately accepted
certificate-signed predecessor rollback: the closest older corrected app is
ad-hoc signed and may prompt for Keychain approval. The known
`pre-optional-callback-fix` bundle has a sign-in fault and is not a functional
rollback.

The isolated candidate branches from `f26e3c48`. It adds only the local
manual Codex view, its reviewed question/pending/bridge code, focused tests
and the twelve stdlib-only bridge modules that the earlier v16 pilot bundled.
Normal UI hides the button; only `--aster-local-codex-manual` exposes it.
It does **not** add the older API-backed delegation views, automatic routing,
tool grants or a new gateway worker. The current `AsterClient.swift`,
`AuthManager.swift`, `AsterCompanionApp.swift` and auth tests are byte-for-byte
unchanged from `f26e3c48`. `ContentView.swift` adds a gated button and sheet;
it does not remove or alter the OpenBao panel, seal confirmation, unseal
submission or passkey-verification path. The existing stable-signing logic
remains; the build script adds bridge packaging, an explicit stable-signing
requirement option and an opt-out for Launch Services registration during
offline builds.

Offline checks passed on 2026-10-12:

- `swift test`: 38 tests, zero failures, including current auth, AI-PAM and
  the added manual Codex bridge/pending tests.
- `git diff --exit-code f26e3c48 --` over the current client, auth manager,
  app delegate and auth tests: no differences.
- `bash -n` for the bundle script and syntax compilation of all twelve
  bridge modules: pass.
- `ASTER_SIGN_IDENTITY=- ASTER_REGISTER_APP=0 ./build-app.sh debug`: built an
  **ad-hoc signed, offline** bundle in the isolated worktree. Strict deep
  signature verification passed. Its `LocalCodexBridge` contained exactly the
  twelve allowlisted modules, byte-equal to candidate sources, with aggregate
  module SHA-256
  `285691dbc637527a9e7b39e42a4bfc5fa1927f676f4388b926799d34c6f04c41`.
  The app was not installed, launched or registered as a URL handler.

This closes the *source-combination feasibility* check, not the D3 release
gate. Before installation, the app owner and Stream A must review the exact
candidate, preserve a **verified signed copy of the currently working app**
as the rollback, verify the owner-held signing identity, and build a signed
release artifact. Then run ordinary sign-in, OpenBao read/status and recovery
path checks, hidden/flagged Codex UI checks and natural refresh observations
on that exact composite build. Do not seal OpenBao merely as a test; do not
send another model question just to prove the UI exists. Any unexpected
Keychain prompt, sign-in regression or OpenBao behavior is a hold/rollback.
