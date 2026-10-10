# D3 native Companion reliability gate — partial live result

**Status: one supervised send, idle restart and short sleep/wake observed;
active-turn interruption not tested.** Owner: Jason. The [executed installation
record](D3-native-manual-v15-installation-2026-10-09.md) controls current
state. Version 15 is installed in ordinary mode with manual sending hidden;
signed version 13 is retained as a rollback copy. The twelve fixed fictional
cases and the additional Vega-light question must not be resent. This gate
tests the delivery path, not sysadmin competence or automatic routing.

**Current blocker:** the Vega turn completed before a controlled interruption,
so the active-turn recovery criterion remains open. Do not send a replacement
question just to force that outcome. A future live recovery experiment would
need a new exact preregistered non-sensitive question, explicit cloud consent,
an interruption method that cannot create duplicate turns, and separate owner
review. Do not bypass the finite UI or reset its saved index.

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

## Original bounded test sequence (historical plan)

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
   are separately reviewed.** Proposed text: “Fictional smart-home light Vega
   reports on, but the room is dark. No power, sensor or network check has been
   run. State what is known and unknown and suggest read-only checks. Do not
   claim to control or repair it.” Use this one non-sensitive question with no
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

## Local candidate checkpoint (historical pre-install state)

`LocalCodexManualView` is behind `--aster-local-codex-manual`, which the
installed app does not use. It requires text review and a separate ChatGPT
consent toggle for each send. `LocalCodexManualPending` writes a private,
content-free request ID before helper launch; a crash or uncertain result
blocks new sends. A recorded completed turn can be read back without new
inference. If the journal instead says `unknown` or `running` but contains an
exact turn ID, a separate explicit “Check original Codex turn” action may
verify that same turn's full completed snapshot and only then mark the local
journal completed. It rejects tool items and does not start a new turn. An
absent turn ID, incomplete original turn, mismatched owner/ID or concurrent
bridge lock remains unresolved. The helper remains pinned to a ChatGPT account, read-only
sandbox, disabled web, zero MCP servers, one turn and no automatic retry.

All 55 native tests pass, including two private-record tests. An unregistered,
uninstalled ad-hoc debug bundle passed strict signature verification; its
executable SHA-256 is
`741716e2fb402c93ec8a96c269cc6208afc9ec29fc357c8c577499dab6837fd1`.
Its metadata-only preflight returned `inference=false` and the pinned manifest
SHA-256 `34d349045dea8ae8410ccc984e508f1754348539f0491fe542e0bd31f78b3753`
with ChatGPT auth and `gpt-5.6-luna` medium. No model turn, real credential
readout, app installation or Launch Services registration occurred. This is
a source/build checkpoint, not a routine-use release.

After review found that a locally `unknown` turn with a recorded Codex turn
ID could be verifiably completed yet remain inaccessible, a new offline
reconciliation candidate was added. Fifteen focused Python tests pass,
including successful exact-turn promotion and rejection of a snapshot with a
tool item. This changed the bridge source hash and supersedes the initial
manifest above. The current metadata-only source preflight returned
`483062186349703ee472b51323c88fb4ffa1f780ae9ff6f351d4046da4973392`;
the manual view now pins that value. The earlier ad-hoc bundle has not been
installed and is not the current candidate. A fresh unregistered, uninstalled
ad-hoc bundle passed strict signature verification with executable SHA-256
`0b6571806e679282183af98168d28ff103167d6977401d36742a3bb261a23207`.
Its **bundled** metadata-only preflight returned the pinned manifest above
with `inference=false`; all 55 native tests passed. A stable-signed release
artifact, exact installation/rollback review and live gates are still required.

## Execution addendum — 2026-10-09

Jason approved one version-15 installation and, after an inconclusive first
entry with two concurrent app instances, one clean single-instance retest.
The normal app signed in after one first-entry Keychain prompt. Aster showed
AI-PAM approvals and the disabled-by-default manual request view. Jason
reviewed the exact Vega question and cloud destination, consented in the app,
and clicked Send once. Its original answer completed and displayed under one
request ID; the content-free journal advanced from 13 to 14 completed rows.
The answer arrived before the app could be interrupted, so step 3 above is
**not passed**. No replacement question was sent.

After Jason finished with the answer, the app reopened unflagged to normal
Aster, with manual sending hidden and no visible Keychain prompt. Jason then
initiated one ordinary sleep/unlock. The same process remained signed in,
AI-PAM showed no pending approvals, the journal remained unchanged, and Jason
reported no Keychain or sign-in prompt. These are narrow restart and short
sleep/wake observations; they do not prove natural token refresh, long-duration
reliability, general manual release or active-turn recovery. The earlier
version-13 and uninstalled-candidate descriptions above are historical and
must not be read as the current deployment state.

A subsequent read-only check reopened the signed app in manual mode and found
the same saved Vega request ID marked completed. **Recover original answer**
displayed that turn's original answer after restart; the journal still held
14 completed rows and no new question was sent. The app was returned to
ordinary unflagged mode afterward. This narrows the recovery gap to
interruption while a turn is running or its outcome is uncertain. It does not
close that gap or justify another live question without a new test gate.
