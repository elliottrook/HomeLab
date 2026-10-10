# D3 native manual Codex version-15 release candidate

**Status: signed local candidate; not installed or launched.** Owner: Jason.
This is a proposal for one bounded reliability test, not routine Ask Codex
release, automatic routing, sysadmin delegation or a tool grant.

## Exact candidate and current app

| Item | Read-only or local-build evidence |
|---|---|
| Current app | `/Applications/AsterCompanion.app`, version 13, executable SHA-256 `c3b016f41045a636c0503af2b7448a5f255f54dcd859a61f6dbb5fc84221394c` |
| Candidate | `apps/AsterCompanion/.build/out/Products/Debug/AsterCompanion.app`, version 15, executable SHA-256 `f83ed9fe74c33222beb39a73519644c5b6fd796e991e6f0f6c598cca950936b1` |
| Signing | Both bundles pass strict signature verification and have the same designated requirement: `com.elliottrook.aster-companion` under the existing local code-signing certificate fingerprint `10B67A3B122FAFCDB2BB55124CAF327115A4E6FA`. This did **not** prevent a Keychain prompt on the earlier version-14 update. |
| Codex preflight | The **signed candidate's bundled script** returned `inference=false`, manifest SHA-256 `483062186349703ee472b51323c88fb4ffa1f780ae9ff6f351d4046da4973392`, ChatGPT account, `gpt-5.6-luna` medium, read-only sandbox, disabled web and zero MCP servers. No question was sent. |
| Tests | 55 native tests and 15 focused local-bridge tests pass. A broader 266-test discovery attempt on system Python had 13 import/environment errors for missing `httpx`/`pydantic`; no dependencies were installed. |

The candidate adds a hidden, manual native question surface. A private
content-free pending record is written before the helper starts. One reviewed
question and an explicit ChatGPT consent toggle are required. If the app dies,
the same request ID remains blocked from resubmission. A completed original
turn can be recovered without inference; an uncertain row with a recorded
turn ID can be reconciled only after the exact full Codex snapshot proves
completion and contains no tool item. No model, skill or policy is selected
automatically.

## Proposed single installation and test

1. Confirm no request is active, current version-13 signature/hash and
   aggregate private-journal state. Quit Companion. Make a fresh, hash-checked
   binary rollback copy at
   `/Applications/AsterCompanion.pre-manual-v15-20261009.app`; do not alter
   the Keychain item or copy token values.
2. Copy only this signed version-15 bundle into the normal application path,
   verify the installed executable hash and signature, and start it with the
   explicit `--aster-local-codex-manual` flag. Check ordinary Aster sign-in,
   AI-PAM read-only status, and the manual surface before sending anything.
   Count any Keychain prompt separately for update, normal launch and refresh.
3. Jason reviews the exact fictional Vega-light question in the
   [reliability gate](D3-native-live-reliability-gate-2026-10-09.md) and
   explicitly consents in the app. Send once under a new request ID. If it
   completes before interruption, record an inconclusive interruption test;
   do not send a replacement to obtain a preferred outcome. Otherwise,
   interrupt only Companion, reopen it and use the recorded ID to inspect or
   reconcile the original turn. Never resend that ID.
4. Check normal Aster operation after recovery. Leave the manual mode disabled
   for routine use until independent answer review, natural refresh and the
   agreed sleep/wake/restart evidence have passed a separate release decision.

**Stop:** unexpected tool/approval event, unreviewed cloud send, duplicate
turn, exposed credential, normal-assistant regression, repeated Keychain
prompt during ordinary use, or an unexplained journal/turn mismatch. On stop,
preserve the journal and Codex IDs; do not clear an uncertain pending record.
Restore the version-13 bundle if normal use regresses. A binary rollback is
available, but prior testing showed that an older bundle can open with a
stale/revoked session; a usable authenticated rollback is **not guaranteed**.
If version 13 cannot authenticate after restoration, stop and use the normal
human sign-in path rather than copying or altering refresh tokens.

This plan does not authorize installation, a Keychain ACL change, Mac sleep,
a Codex model turn, infrastructure access or a Git push. The candidate and
current app remain separate until Jason reviews the exact live gate.
