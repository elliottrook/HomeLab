# D3 Companion test window — 2026-10-25

> Result: **ORDINARY COMPANION PATH PASS; AI-PAM MANAGEMENT AUTOMATION INCONCLUSIVE**

Jason confirmed that Companion was not in use and authorized the tests needed
today. This window permits a bounded quit/relaunch, authenticated read-only UI
checks, synthetic recovery/error presentation and a small number of uniquely
identified ordinary requests if needed. It does not enable automatic routing,
change OpenBao state, grant a tool or release the deferred manual-Codex path.

## Installed artifact

- Installed application: `/Applications/AsterCompanion.app`
- Version/build: `0.3.0` / `16`
- Bundle identifier: `com.elliottrook.aster-companion`
- Signer: `Aster Companion Local Signing 2026 R2`
- Executable SHA-256:
  `7b968e5fdf11f88f2105c2d65cf3468dd27b8f245e787e73acdc8dfc2032124c`
- Strict/deep signature verification: pass

The executable digest exactly matches the accepted two-Mac release record in
`Aster-Voice-V1-Release-Manifest.json` and the launch-crash correction evidence.
It is not the superseded crashing bundle.

All twelve installed `LocalCodexBridge` Python modules are byte-identical to
the current reviewed repository files. The installed native executable predates
two later conservative `DelegationView` wording changes: `running` is now
labelled as a last report, and `unknown` ignores conflicting server prose and
instructs the owner not to resend. Those source changes therefore require a
future reviewed build/install boundary; this test does not claim they are in
the installed binary.

## Completed checks

| Check | Result |
| --- | --- |
| Current native Swift suite | 60/60 passed |
| Installed bridge inert mode | `enabled=false`, `inference=false` |
| Installed bridge metadata-only preparation | Passed; one-turn, read-only sandbox, web search disabled, zero MCP servers, no automatic retry, no durable content |
| Installed bridge recovery preflight | `recovery_ready=true`, `inference=false` |
| Public health route | HTTP 200; `aster-agent` / `ok` |
| Unauthenticated personas route | HTTP 401, fail closed |
| Unauthenticated OpenBao status route | HTTP 401, fail closed |
| Platform lease | `ready` |
| Aster Agent / accepted llama.cpp SYCL / Speech services | active / active / active |
| Signed app launch | Process remained alive through the initial soak; no new crash report was present |
| Persisted-session relaunch | Passed twice; returned directly to signed-in normal mode without a Keychain prompt |
| AI-PAM approvals | Loaded successfully; no pending approvals |
| Read-only OpenBao status | Saved session correctly failed closed with HTTP 401; one fresh passkey flow then reported `OpenBao is unsealed` |
| Recorded delegation | New requests remained closed; expired completed answer said `Do not resend`; unavailable recovery said `No retry was sent` |
| Ordinary Aster request | One content-free request returned exact `COMPANION_OK` in 2.8 seconds (1,691 input / 5 output tokens; 55.0 tok/s) |
| Pending ARR action check | Read-only query returned `No pending ARR action right now`; no approval or execution control was used |

The launch occurred while the Mac login session was locked. The only observed
error-level messages were macOS App Intents failures to contact
`com.apple.linkd.autoShortcut`; no Aster request, authentication, voice,
OpenBao or bridge failure was logged. Treat those messages as a locked-session
OS integration observation, not proof of a user-path failure.

## Live UI result

The normal surface restored its existing session after launch and after two
bounded quit/relaunch cycles. No Keychain prompt appeared. AI-PAM's Approvals
tab loaded with no pending approvals. OpenBao status correctly rejected the
non-fresh session, opened the required passkey flow and then reported the
service unsealed. No token was entered, and neither unseal nor seal was
invoked.

The recorded Codex surface remained fail closed. Submission was disabled with
the explicit notice that new requests are closed. Selecting an existing
completed request whose temporary answer had expired produced the fixed
`Do not resend` instruction. A second recorded request reported that recovery
status was unavailable and that no retry was sent. No Codex question, recovery
request or cancellation was submitted.

One unique content-free ordinary request asked for exact text
`COMPANION_OK`. The app showed its context-reading phase and returned that
exact answer in 2.8 seconds. This proves the current signed-in typed request
path against the accepted llama.cpp/SYCL service for this observation; it is
not an NLU, voice, automatic-routing or answer-quality benchmark.

The separate pending ARR action check returned no pending action. No proposal,
approval or execution request was created or consumed.

## AI-PAM Management observation

Selecting AI-PAM's Management tab twice disconnected the Computer Use
accessibility channel. The first attempt coincided with repeated AppKit
`Invalid view geometry` runtime diagnostics; the second produced no new
Companion error-level entry. In both cases the app process stayed alive and a
graceful quit/relaunch restored the normal signed-in screen without a Keychain
prompt. This does not establish whether a human-visible Management rendering
fault exists. Treat it as a bounded automation/display observation requiring a
future direct visual check, not as a reason to change authority controls or to
guess at a source fix.

Companion was left running in normal signed-in mode with the OpenBao panel and
all sheets closed. Today's result strengthens ordinary Companion reliability
and recorded-job handling. It does not release the hidden manual-Codex path,
enable automatic routing, grant a tool or change D3's safe hold.
