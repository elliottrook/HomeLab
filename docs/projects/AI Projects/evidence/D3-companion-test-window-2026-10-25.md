# D3 Companion test window — 2026-10-25

> Result: **STATIC AND NON-UI CHECKS PASS; LIVE UI CHECKS PENDING AN UNLOCKED SESSION**

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

The launch occurred while the Mac login session was locked. The only observed
error-level messages were macOS App Intents failures to contact
`com.apple.linkd.autoShortcut`; no Aster request, authentication, voice,
OpenBao or bridge failure was logged. Treat those messages as a locked-session
OS integration observation, not proof of a user-path failure.

## Pending live UI checks

After the Mac session is unlocked:

1. confirm the app presents the signed-in normal Aster surface without a new
   crash or unexpected Keychain loop;
2. inspect the authenticated AI-PAM and read-only OpenBao status surfaces,
   without submitting an unseal token or invoking seal;
3. inspect recorded delegation/recovery presentation without resending any
   uncertain request;
4. submit at most one uniquely identified ordinary Aster request only if the
   existing UI state cannot establish the ordinary path; and
5. leave Companion in normal mode and record whether a Keychain/passkey prompt
   appeared.

Until those checks complete, this evidence does not change D3's safe hold or
the automatic-routing gate.
