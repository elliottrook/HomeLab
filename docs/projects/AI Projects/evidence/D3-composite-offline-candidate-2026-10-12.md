# D3 Companion composite: offline candidate, not a release

**Status: local candidate `eb69280` on `codex/aster-companion-composite`; no
installation, remote push or Codex question.** This candidate responds to
Jason's requirement that the native OpenBao seal/unseal controls survive the
manual Codex integration. The current installed app remains untouched.
The browser Companion's existing OpenBao controls and service endpoints are
also preserved: this candidate changes neither its web UI nor its service.
The new manual Codex view is Mac-only; browser-side Codex handoff is a
separate scope and is not claimed here.

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
- `ASTER_SIGN_IDENTITY='Aster Companion Local Signing 2026'
  ASTER_REQUIRE_STABLE_SIGNING=1 ASTER_REGISTER_APP=0 ./build-app.sh release`:
  built an offline release bundle. Strict deep signature verification passed;
  its designated requirement uses the same bundle identifier and certificate
  root (`10b67a3b122fafcdb2bb55124caf327115a4e6fa`) as the installed app.
  Its executable SHA-256 is
  `c287a4f1743618872eb98bcf05a07da76f46d0fde9dbdd0f3f912208f4123c24`.
  The bundled bridge still contains exactly the twelve byte-equal allowlisted
  modules with the aggregate SHA-256 above. This bundle was not installed,
  launched or registered as a URL handler.
- An intact copy of the currently working installed app was placed at
  `/Users/jelliott/lab/private-backups/aster-companion/pre-composite-20261012.app`.
  The source and copy both passed strict deep signature verification; all
  eighteen relative bundle entries matched by type, size and SHA-256, and the
  executable SHA-256 remains `7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
  This is a verified local rollback copy, not a completed restore-and-launch
  drill or proof of off-site backup.

This closes the *source-combination feasibility* check, not the D3 release
gate. The app owner reviewed the source candidate and found no direct conflict
with passkey, OpenBao or Keychain code, but did not give live acceptance. The
stable-signed release build and verified local rollback copy are prepared.
Before installation, pin the exact release artifact and rollback, then run
ordinary sign-in, OpenBao read/status and recovery
path checks, hidden/flagged Codex UI checks and natural refresh observations
on that exact composite build. Do not seal OpenBao merely as a test; do not
send another model question just to prove the UI exists. Any unexpected
Keychain prompt, sign-in regression or OpenBao behavior is a hold/rollback.
