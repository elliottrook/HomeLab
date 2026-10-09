# D3 native original-answer recovery candidate — 2026-10-09

Status: local candidate, uninstalled. No new model turn, worker activation,
Keychain ACL change, production service change, or Git push was made.

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
Server. It rechecks the pinned ChatGPT account/configuration fingerprint and
uses a client allowlist containing `thread/read` but no `turn/start`. It accepts
only a full snapshot of that exact completed turn with one final answer and no
tool items. The native UI requires the answer to be shown and acknowledged
before advancing. A content-free `recovered` event must be saved first.

## Local evidence

- Focused Python CLI/recovery tests: 6 passed. They reject mismatched thread,
  missing turn, partial snapshot and tool items, and assert that the recovery
  path calls only configuration read and exact thread read.
- Native Companion suite: 47 passed. The uninstalled candidate builds and
  passes strict code-signature verification.
- A metadata-only preflight of the bundled helper returned manifest SHA-256
  `eb36910ebf0762d5bc9aedab4892a7122a217f5a1c0ad4c9e41e3795862755ee`,
  matching the pinned UI value. Its observed constraints were ChatGPT auth,
  `gpt-5.6-luna` medium, read-only sandbox, disabled web, zero enabled MCP
  servers, one model turn maximum and no automatic retry.
- One read-only CLI recovery of the already completed fictional case returned
  `completed`, `inference=false`, `automatic_retry=false` and a non-empty
  original answer. The answer text was not printed in the command result. The
  original case was not resent.
- Current installed app executable SHA-256:
  `95c8d0254eea14f8d75486c24da326f2c0b365e5e3c28da9ac409ae18e07f62c`.
  Uninstalled candidate executable SHA-256:
  `2a64f1fdebff20f3158ff0fc6d5b3c3e5b49c491d38f8e6a778cee281151a65b`.
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
