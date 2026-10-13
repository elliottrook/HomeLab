# D3 Companion composite: candidate and Mac-mini install gate

**Status: local candidate `eb69280` on `codex/aster-companion-composite`;
installed on the Mac mini by Jason's explicit approval. Signed-in UI,
read-only OpenBao status, AI-PAM panel and one ordinary Aster answer pass;
natural refresh on this binary remains untested but is [monitored rather than
an indefinite blocking gate](D3-refresh-gate-reassessment-2026-10-12.md).
No remote push or manual
Codex question.** This candidate responds to
Jason's requirement that the native OpenBao seal/unseal controls survive the
manual Codex integration. The previous installed app remains intact as a
local rollback copy.
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
  This was a separate debug build; it was not installed or launched.
- `ASTER_SIGN_IDENTITY='Aster Companion Local Signing 2026'
  ASTER_REQUIRE_STABLE_SIGNING=1 ASTER_REGISTER_APP=0 ./build-app.sh release`:
  built an offline release bundle. Strict deep signature verification passed;
  its designated requirement uses the same bundle identifier and certificate
  root (`10b67a3b122fafcdb2bb55124caf327115a4e6fa`) as the installed app.
  Its executable SHA-256 is
  `c287a4f1743618872eb98bcf05a07da76f46d0fde9dbdd0f3f912208f4123c24`.
  The bundled bridge still contains exactly the twelve byte-equal allowlisted
  modules with the aggregate SHA-256 above. This release bundle was later
  installed on the Mac mini with the manual screen hidden in normal mode.
- An intact copy of the currently working installed app was placed at
  `/Users/jelliott/lab/private-backups/aster-companion/pre-composite-20261012.app`.
  The source and copy both passed strict deep signature verification; all
  eighteen relative bundle entries matched by type, size and SHA-256, and the
  executable SHA-256 remains `7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
  This is a verified local rollback copy, not a completed restore-and-launch
  drill or proof of off-site backup.

**Installation checkpoint, 2026-10-12 Vancouver:** Jason explicitly approved
installing this Mac candidate and checking ordinary behavior. The source
release bundle was copied into `/private/tmp`, strict-deep signature verified
again, and its executable hash matched `c287a4f...`. The then-current
`/Applications/AsterCompanion.app` was renamed to
`/Applications/AsterCompanion.pre-stream-a-20261012.app`; the staged release
was moved into `/Applications/AsterCompanion.app`. Both installed and prior
bundle signatures verified. Executable hashes are respectively
`c287a4f1743618872eb98bcf05a07da76f46d0fde9dbdd0f3f912208f4123c24`
and `7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
The app launched and remained a running process. The Mac was initially locked;
after Jason unlocked it, the installed app showed a signed-in normal Aster
screen. Its manual Codex button was absent in normal mode. The OpenBao panel
initially showed a 401 requiring a fresh passkey. Jason completed the macOS
Passwords prompt privately; the panel then reported **OpenBao is unsealed**
with its unseal-token field disabled. The AI-PAM panel opened and showed no
pending approvals. Returning to the normal view showed the Aster input and
mode picker intact. These UI/read-only checks did not prove an ordinary
answer or natural token refresh. No OpenBao seal/unseal operation was sent.

Jason then explicitly allowed one model question to finish ordinary-use
validation. In normal **Sysadmin Aster** mode, Stream A sent only the
non-personal question “What is 2 + 2? Reply with the number only.” The app
displayed “4” with a 2.8-second elapsed indicator. The visible UI shows a
successful ordinary chat response; it does not by itself prove which backend
served it or measure broader answer quality. The hidden manual Codex surface
was not used. Do not call this the full D3 release gate: flagged manual-surface
behavior on this exact binary remains unobserved, while natural refresh is a
separate reliability observation.

This closes the *source-combination feasibility* check, not the D3 release
gate. The app owner reviewed the source candidate and found no direct conflict
with passkey, OpenBao or Keychain code, but did not give live acceptance. The
stable-signed release build and verified local rollback copy are prepared.
The owner subsequently reviewed the release evidence and reported no further
technical blocker. Normal signed-in UI, read-only OpenBao status/passkey
verification and one ordinary Aster answer now pass on the installed build;
longer-term refresh and Keychain behavior still require observation.
The manual Codex surface remains hidden during normal use. The web
OpenBao route tests could not run in this isolated macOS Python environment
because `fastapi` is not installed; no dependency was installed for this
documentation check. The web source and its test file are byte-for-byte
unchanged from the pinned Companion baseline.
Before routine manual-Codex release, verify the flagged pilot UI without
unnecessary new questions and confirm recovery behavior using existing
recorded work. Continue to monitor natural refresh and Keychain behavior in
ordinary use; do not wait indefinitely for them before unrelated Stream A
work. Do not seal
OpenBao merely as a test. Any unexpected
Keychain prompt, sign-in regression or OpenBao behavior is a hold/rollback.

## Later read-only binary check — 2026-10-13

The installed app still passes strict deep code-signature verification and
retains executable SHA-256 `c287a4f1743618872eb98bcf05a07da76f46d0fde9dbdd0f3f912208f4123c24`.
A read-only strings check finds the compiled `--aster-local-codex-manual` flag,
manual-review heading, exact-text ChatGPT consent toggle, send button and
recorded-turn recovery labels.
Both preserved predecessor bundles pass strict deep signature verification and
retain executable SHA-256 `7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
This confirms the expected binary and rollback artifacts remain present; it
does **not** prove the flagged UI, consent interaction or a functional rollback
launch. The Mac was locked when the UI check was attempted, so those release
gates remain open. No app launch, model question, credential read or OpenBao
action was performed in this check.
