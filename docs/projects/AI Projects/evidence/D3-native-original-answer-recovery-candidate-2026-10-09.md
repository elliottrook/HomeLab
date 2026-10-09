# D3 native original-answer recovery candidate — 2026-10-09

Status: locally installed after Jason's approval on 2026-10-09; case 1 original
answer recovered and displayed in Companion. No new model turn,
worker activation, Keychain ACL change, production service change, or Git push
was made.

## Trigger and result

The first finite fictional case completed, but after normal Companion restart
its volatile answer disappeared while the saved request ID correctly blocked a
repeat dispatch. The old UI could neither display the original answer nor
advance. This candidate adds a **Recover original answer** control for a
recorded completed turn. Recovery is read-only and returns the final answer
through a private pipe; it never starts a thread or model turn, retries the
question, or touches the older worker credential.

The helper checks the owner-only dispatch database for the exact request ID,
completed state, recorded thread and recorded turn before starting Codex App
Server. Recovery checks ChatGPT authentication, OpenAI provider, read-only
sandbox, disabled web and zero enabled MCP servers. It does not pin the current
model or Codex binary version, which may have changed since the original turn;
new sends still require the full reviewed manifest. Recovery uses a client
allowlist containing `thread/read` but no `turn/start`. It accepts
only a full snapshot of that exact completed turn with one final answer and no
tool items. The native UI verifies that the saved request was submitted for the
currently displayed case and requires the answer to be shown and acknowledged
before advancing. A content-free `recovered` event must be saved first.

## Local evidence

- Focused Python CLI/recovery tests: 6 passed. They reject mismatched thread,
  missing turn, partial snapshot and tool items, and assert that the recovery
  path calls only configuration read and exact thread read.
- Native Companion suite: 49 passed. The uninstalled candidate builds and
  passes strict code-signature verification. Its bounded output pipe now
  accommodates JSON escaping of the maximum permitted recovered answer, and
  the overflow rejection test still passes.
- A metadata-only preflight of the bundled helper returned manifest SHA-256
  `08c51aae6afe227c5b66918db3e57f54e77a29eb7306de3182fdf84091ae05f5`,
  matching the pinned UI value. Its observed constraints were ChatGPT auth,
  `gpt-5.6-luna` medium, read-only sandbox, disabled web, zero enabled MCP
  servers, one model turn maximum and no automatic retry.
- A recovery-only metadata check passed without requiring the current model
  to exist. A read-only CLI recovery of the already completed fictional case returned
  `completed`, `inference=false`, `automatic_retry=false` and a non-empty
  original answer. The answer text was not printed in the command result. The
  original case was not resent.
- Current installed app executable SHA-256:
  `95c8d0254eea14f8d75486c24da326f2c0b365e5e3c28da9ac409ae18e07f62c`.
  Uninstalled candidate executable SHA-256:
  `814a0fd4e01d3179e9b5cf6c0208f428895ea7798c905b55508b88146da0a075`.
- Independent review found model/binary drift and saved-case binding risks.
  The local candidate was revised for both and the real `thread/read` shape
  was checked through a read-only recovery of case 1. Follow-up review found
  no blocking issue and one bounded-output issue, which was fixed and tested.
  The code does not request the Aster worker Authentik Keychain credential;
  Codex app-server authentication may use separate local credential storage.
- The broad delegation Python discovery run used the macOS system Python and
  failed to import existing `httpx`/`pydantic` dependencies. It is not counted
  as a passing suite. No dependency was installed for this candidate.

## Release and rollback gate

Before replacement, independently review the exact source diff, preserve a
fresh rollback copy of the installed app and its hash, and verify the signed
candidate hash and manifest again. The normal Companion must close cleanly;
install only the candidate app, then reopen normal mode first. Confirm normal
sign-in, AI-PAM and Aster conversation without using the evaluation flag. A
Keychain dialog for Companion sign-in may occur because builds are ad-hoc
signed; do not grant the generic `security` tool standing access to the worker
credential. If normal mode regresses, restore the fresh rollback copy and
reconcile before any new test.

Only after normal-mode validation, open the finite evaluation flag, recover
case 1 by its saved request ID, verify the displayed original answer, and
acknowledge it. That is a read-only recovery. Do not send case 2 as part of
this release gate. A separate reviewed gate remains required for the remaining
eleven fictional questions and independent label review. The candidate does
not establish general Ask Codex release or automatic routing.

## Installation checkpoint — 2026-10-09

Jason approved replacing the installed app for case 1 recovery only. Before
replacement, the old app was copied to
`/private/tmp/AsterCompanion.pre-D3-recovery-20261009.app` and moved to
`/Applications/AsterCompanion.pre-D3-recovery-20261009.app`; both rollback
executables match the recorded old SHA-256 above. The installed app executable
matches the candidate SHA-256 above and passes strict code-signature
verification. Normal Companion opened after Jason resolved the macOS Keychain
startup wait: its signed-in Aster composer, AI-PAM approvals screen (no pending
approvals), and Codex requests screen were visible. The latter still showed
closed submission with recorded completed requests. No new Aster conversation
was sent as part of this smoke check.

The app was then relaunched with the finite evaluation flag. Startup again
paused at `AuthManager.init` → `KeychainStore.get("oidc_session_v2")` →
`SecItemCopyMatching`. A process stack sample established this wait without
reading the token. Jason resolved the macOS prompt, and Companion opened the
saved case 1 request. The UI offered **Recover original answer** rather than
a send action. One click displayed the original completed HTTP 503 answer and
the private metadata log appended `recovered` after `submitted` and
`completed`. No new `submitted` event appeared. The displayed answer met the
case 1 rubric on a preliminary human-readable check; independent label review
remains outstanding. The UI remains on case 1 awaiting acknowledgement. Case 2
has **not** been sent. The older `/usr/bin/security` worker credential did not
receive standing access.
