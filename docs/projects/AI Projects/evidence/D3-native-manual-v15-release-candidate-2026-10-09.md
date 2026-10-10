# D3 native manual Codex version-15 release candidate

**Status: clean single-instance retest completed one reviewed turn; interruption
recovery remains untested.** Owner: Jason. See the
[installation checkpoint](D3-native-manual-v15-installation-2026-10-09.md).
This remains a candidate for a bounded reliability test, not routine Ask
Codex release, automatic routing, sysadmin delegation or a tool grant.

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

Jason approved the first installation and bounded test, then clarified that
two Keychain prompts can occur during entry and that the candidate entered
after the second. The first attempt was stopped conservatively before any
model send. A sandboxed launch produced the sole crash report, while a
normally launched manual instance remained running. An accidental second
unflagged instance makes the prompt count inconclusive. A future attempt must
ensure exactly one Companion process before launch, distinguish prompts on
first entry from prompts during subsequent ordinary use, and confirm normal
operation before a question is sent. No Keychain ACL change, Mac sleep,
infrastructure access or extra Git push is authorized by this document.

Jason approved that single-instance retest. The same signed version-15 bundle
was installed, one flagged process launched, one first-entry Keychain prompt
was reported, and normal Aster, AI-PAM approvals and the manual surface were
visible. After Jason's in-app review and consent, the fictional Vega-light
request completed once and displayed its original answer; the content-free
journal advanced from 13 to 14 completed rows. It finished before an
interruption could be made, so the recovery criterion is still open. The
answer was handed to Jason; no replacement request will be sent to force a
recovery trial. After he finished with it, the completed view was closed
without enabling a new question. An idle restart without the manual flag
returned to signed-in normal Aster, showed no visible Keychain prompt, and
hid the manual-send control. This remains a narrow UI/dispatch result, not a
routine-use or active-turn recovery release.

Jason then performed one normal Mac sleep/unlock. The same ordinary Companion
process remained running and signed in, the journal remained at 14 completed
rows, manual sending stayed hidden, and Jason reported no Keychain or sign-in
prompt. This short observation does not establish natural token-refresh or
long-duration reliability.

The same completed Vega request was later recovered read-only in the native
manual view after restart, without a new journal row or new question. The app
was returned to ordinary mode with manual sending hidden. Recovery from an
active or uncertain turn remains untested.
