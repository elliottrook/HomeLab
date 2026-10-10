# D3 native manual Codex version-15 installation checkpoint

**2026-10-09, supervised gate in progress.** This records the installation and pre-send state only. It is not a release decision or evidence of a successful live turn.

- Jason approved the specific Forgejo push and bounded native version-15 test. Commit `99409701b70b0f91a66a150ec65cc9f98527a22d` was pushed to Forgejo `origin`; the GitHub mirror was later read back at the same SHA. No direct GitHub push occurred.
- Before installation, `/Applications/AsterCompanion.app` was version 13, strictly signed, with executable SHA-256 `c3b016f41045a636c0503af2b7448a5f255f54dcd859a61f6dbb5fc84221394c`. The private Codex journal contained 13 `completed` rows and no other recorded states. The ordinary Companion screen was visible and signed in. No historical request text or token was read.
- The version-13 rollback copy is `/Applications/AsterCompanion.pre-manual-v15-20261009.app`; its hash and strict signature were verified before the swap. The original version-13 bundle also remains at `/Applications/AsterCompanion.pre-manual-v15-original-20261009.app`.
- The version-15 candidate was staged, checked, and installed at `/Applications/AsterCompanion.app`. Its installed executable SHA-256 is `f83ed9fe74c33222beb39a73519644c5b6fd796e991e6f0f6c598cca950936b1`; its strict signature passes and `CFBundleVersion` is 15.
- A sandboxed `open` attempt reported Launch Services `-10827`; sandboxed `lsregister` reported `-10822`, and a direct sandboxed executable attempt aborted inside `_RegisterApplication`. The same `open` command with elevated host access succeeded. These are launch-environment observations, not evidence that the app failed its normal launch.
- A screen-control inspection unintentionally started an unflagged instance. Its exact PID was terminated, leaving only the intended `--aster-local-codex-manual` instance at the time of the process check. The screen-control tool then timed out while inspecting the app, so the native sign-in, AI-PAM and manual surfaces are **not yet verified**. Jason was asked to report the visible screen state without sharing credentials.
- The journal still showed 13 `completed` rows and no new row after launch. No new model question has been sent, no Keychain item has been read or modified, and no infrastructure action has been taken.

**Next gate:** verify the visible normal Aster screen, AI-PAM read-only status and manual question surface. Stop if there is a recurring ordinary-use Keychain prompt or regression. Jason must review the exact fictional Vega-light question and use the app's explicit ChatGPT consent before the one permitted send. Keep the content-free journal and request ID intact through any interruption; do not resend an uncertain turn.

## First-launch interruption and rollback

Jason reported a crash alert over a Keychain prompt. Read-only process and
crash-report checks showed that the alert belonged to the earlier sandboxed
direct-executable attempt, while the deliberately launched manual-test
instance remained alive. An accidental unflagged instance had also been
started by screen-control inspection and was stopped by exact PID. The journal
remained at 13 completed rows.

When Jason reported another Keychain prompt, the conservative repeated-prompt
stop rule was applied: the manual-test process was stopped, the version-15
bundle preserved at
`/Applications/AsterCompanion.manual-v15-stopped-20261009.app`, and the exact
version-13 original returned to `/Applications/AsterCompanion.app`. Its hash,
strict signature and version were verified. Version 13 reopened to its signed-in
normal screen. No new Codex request was sent.

Jason then clarified that it often asks for two prompts before entry and that
version 15 entered after the second prompt. Thus this observation does **not**
establish recurring prompts during ordinary use or an application crash in the
normally launched version 15. Two concurrently launched app instances are a
plausible cause of the paired prompts, but that is unproved. The gate needs a
single-instance retest that counts first-launch prompts separately from later
ordinary-use prompts. Do not infer successful reliability from this attempt.

## Approved single-instance retest

Jason approved a clean retest. Version 13 was confirmed signed in, strictly
signed and at the expected hash. The version-15 stopped bundle retained its
expected hash and strict signature. The private journal still had 13 completed
rows. Version 13 was stopped by exact process ID and preserved at
`/Applications/AsterCompanion.pre-manual-v15-retest-20261009.app`; the existing
independent version-13 rollback copy remained intact. The same version-15
bundle was restored to the normal application path and launched once with
`--aster-local-codex-manual`. Process inspection found one flagged instance
and no second Companion process. Jason reported one Keychain prompt before
entry, then successful sign-in. Screen control showed the ordinary Aster view,
AI-PAM with no pending approvals, and the manual Codex question surface.

The exact fictional Vega-light question from the reliability gate was placed
in the review screen. Jason checked the explicit ChatGPT consent and clicked
Send once. The native surface displayed the completed original answer for
request `request-bc4285fd-5454-400f-9b31-53971c984cb9`. The journal moved
from 13 to 14 `completed` rows with no other states, and the single flagged
Companion instance remained running. The answer text is deliberately not
copied into this evidence record. No home device or infrastructure tool was
granted or called in this test.

The turn completed before an app interruption could be performed. This is
evidence for reviewed one-send delivery and answer display, **not** for
active-turn interruption recovery or routine-use reliability. Do not send a
replacement question to obtain a preferred outcome. Confirm Jason has seen
the answer before closing its view, then verify ordinary Aster use and any
post-entry Keychain prompts. Manual mode remains experimental.

## Answer handoff and ordinary restart

Jason replied that he was done with the displayed answer. The completed-answer
view was closed without choosing “allow a new question.” The normal signed-in
Aster screen remained visible. The single manual-mode process was then quit
while idle and verified absent. Version 15 was reopened without
`--aster-local-codex-manual`; process inspection found one unflagged instance.
Screen control showed the signed-in ordinary Aster view, the AI-PAM approvals
sheet showed no pending approvals, and the Codex requests sheet did not expose
the manual-send button. No Keychain prompt was visible during this ordinary
restart. This verifies UI availability and feature gating, not an end-to-end
ordinary Aster answer or a full refresh/sleep-wake reliability window.

Version 15 remains installed and running in ordinary mode. The exact version-13
rollback copy at `/Applications/AsterCompanion.pre-manual-v15-20261009.app`
remains available. The active-turn interruption, independent answer review,
natural refresh and sleep/wake criteria remain open; no routine manual-Codex
release or automatic routing is claimed.

## Owner-initiated sleep/wake observation

Jason reported that he had put the Mac to sleep and unlocked it. A read-only
check afterward found the same single unflagged Companion process still
running, version 15 installed, and the private journal unchanged at 14
`completed` rows with no other states. Screen control showed the signed-in
ordinary Aster view, AI-PAM with no pending approvals, and the Codex requests
sheet with manual sending hidden. No new Codex request was made. Jason
reported no Keychain or Aster sign-in prompt during unlock. This is one short
sleep/wake observation, not a natural token-refresh or long-duration
reliability result.

## Read-only original-answer recovery after restart

After the short sleep/wake check, Companion was quit while idle and launched
once with the manual-test flag. The saved private manual request ID remained
`request-bc4285fd-5454-400f-9b31-53971c984cb9`. The UI reported that the
recorded turn had completed and offered **Recover original answer**, rather
than a new-question Send. That action displayed the same original Vega answer
with the message that it had been recovered from the recorded turn. The
private dispatch journal remained at 14 `completed` rows and no other states.
The completed request was not acknowledged/cleared, so the fail-closed saved
ID remains a guard against accidental resubmission.

The recovery view was closed. Companion was quit and reopened once without the
manual flag; one unflagged process and the signed-in ordinary Aster screen were
observed, and the manual-send control was hidden. No new question was sent.
This verifies post-completion original-answer recovery through the signed
native UI. It does **not** demonstrate recovery from a crash while a model
turn is active, natural token refresh or sustained reliability.
