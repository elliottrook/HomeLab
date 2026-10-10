# D3 native Companion reliability gate — proposed, not run

**Status: awaiting a separate live-test decision.** Owner: Jason. The installed
version-13 Companion is the known working app. The twelve fictional Codex
questions are complete and must not be resent. This gate tests the delivery
path, not sysadmin competence or automatic routing.

**Current blocker:** version 13 admits only the completed twelve fixed cases.
It cannot send a new question for an active-turn interruption. That stage
requires a separately reviewed, signed candidate with one exact thirteenth
fictional question, a new pinned manifest, an installation/rollback plan and
explicit cloud consent. Do not bypass the finite UI or reset its saved index.

## Why this is needed

Offline tests now cover a lost turn-start acknowledgement, journal reopening,
and abrupt fake-process death after a durable dispatch claim. They demonstrate
that the local code refuses duplicate submission for the same request ID. They
cannot show that the signed Companion, macOS Keychain and subscription-backed
Codex recover acceptably after a real app interruption or Mac sleep/wake.
Repeated Keychain prompts during binary updates also remain unresolved.

Read-only preflight on 2026-10-09 found installed bundle version `13`, a
passing strict code-signature check and executable SHA-256
`c3b016f41045a636c0503af2b7448a5f255f54dcd859a61f6dbb5fc84221394c`.
The private dispatch journal had thirteen `completed` rows and no other
recorded states; only aggregate state counts were queried. This does not prove
the app is idle or that macOS authentication will remain prompt-free.

## Bounded test sequence

1. **Read-only preflight.** Confirm no Codex request is active; record the
   installed app hash/signature, current authenticated state and content-free
   journal status. Confirm the working app bundle and its private state remain
   recoverable. Do not inspect token values or historical answer text.
2. **Idle restart and wake.** Quit and reopen the app while no request is
   active. Check normal Aster use, sign-in, AI-PAM read-only status, prompt count
   and any new journal events. For sleep/wake, Jason initiates a normal Mac
   sleep and unlocks it; the test observes the app afterward. Do not change
   macOS lock or Keychain settings.
3. **One active-turn interruption, only after the candidate and exact question
   are separately reviewed.** Use one new short fictional, non-sensitive question with no
   tools. Record its new request ID before send. Interrupt only the Companion
   app during the pending turn, then reopen it. Read the same ID's status and
   original Codex turn; recover that answer if completed, or show `unknown` if
   outcome cannot be proved. Never click Send again for that ID, create a
   replacement ID to hide a failure, or manually clear the journal.
4. **Observe normal use.** Confirm the ordinary assistant still works and
   record any authentication prompt or recovery friction. Do not infer a
   reliability percentage from one trial.

## Pass, stop and rollback

Pass requires at most one Codex turn for the new ID; no tool/approval action;
no unreviewed cloud send; no prompt or answer in the operating journal; an
honest completed/unknown state after interruption; usable normal Aster on
restart; and no unexpected recurring Keychain prompt during ordinary use.
Any duplicate, hidden send, unexpected tool request, exposed credential, or
broken normal assistant stops the gate. An auth prompt is recorded as a
failure of the no-prompt normal-use criterion rather than silently dismissed.

The immediate rollback is to stop this test and leave ordinary Companion use
on the known working version-13 bundle. Preserve the journal and recorded
Codex IDs for read-only reconciliation; never delete them to enable a retry.
Do not install version 14, migrate the session, widen Keychain access, enable
the gateway, grant tools, or change production infrastructure in this gate.

Independent answer scoring, a successful live recovery-path check, and an
explicit routine-use release decision remain separate requirements. This
proposal is not approval to install a new build, run the live interruption or
send a model request.
