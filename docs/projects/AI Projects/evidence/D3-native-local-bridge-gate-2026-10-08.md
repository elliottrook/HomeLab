# D3 — one-question native local Codex bridge gate

**Status: APPROVED; ONE LIVE QUESTION COMPLETED; NORMAL-USE CLOSEOUT PENDING.** Owner: Jason. Stream A
implementation gate. This is an architecture comparison, not D3 graduation or
sysadmin delegation.

## Purpose and decision being tested

Determine whether native Aster Companion can use Jason's existing local Codex
sign-in for one explicitly reviewed, fictional no-tools question without the
gateway worker's Authentik activation, short token, four-minute race or extra
credential copy. A passing trial would support the local bridge as the first
normal native adapter; it would not replace the gateway for voice/remote use.

## Verified preflight baseline

- Installed `/Applications/AsterCompanion.app` is signed build **8**; executable
  SHA-256 `343830529ba2836a741268bb8a1566a8ad093f1a2fb0fc460324eaaa2e07705b`.
  It continues to run the existing experience. The new candidate is **not**
  installed or registered with Launch Services.
- The local, signed and unregistered build **9** candidate is at
  `apps/AsterCompanion/.build/out/Products/Debug/AsterCompanion.app`. Its
  executable SHA-256 is
  `a284b7d2525698c982736d94baa624115dbce3fe72d275fd53dec0567beeddd2`;
  recheck it immediately before installation after the final source commit.
  `codesign --verify --deep --strict` passed.
- The candidate includes exactly twelve allowlisted, stdlib-only Python bridge
  modules; it contains no worker credential, provisioning script or broad tool
  collection. Default helper invocation returns `enabled:false`.
- A metadata-only preflight from the signed bundle under a minimal environment
  passed with ChatGPT authentication, `gpt-5.6-luna` at medium effort, zero
  enabled MCP servers, read-only sandbox and disabled web search. Its exact
  manifest SHA-256 is
  `f5f072f6d7395d0b9b77775155239d87e913c38f2adb6acb6b0e1122c5101cd0`.
  No model turn was started by preflight.
- Synthetic bridge fixture: a fake Codex executable completed one turn, returned
  a final answer, wrote no prompt/answer into the durable SQLite journal, and
  refused a duplicate request ID. Python suite: **296 tests passed**. Native
  fake-process suite: **43 tests passed**, including stdin-only request delivery,
  timeout, bounded output, owner-only journal permissions and symlink refusal.
- The deployed gateway's new submissions and answer recovery are closed; the
  existing worker identity is inactive with zero active grants after the last
  accepted trial. This must be rechecked immediately before any live run.

## Exact bounded action requiring approval

1. Recheck candidate and installed hashes, code signature, metadata manifest,
   gateway closed state, worker inactivity and a verified local backup of build
   8. Stop if any baseline differs materially. Do not read or export secrets.
2. Quit Companion; preserve the current installed build 8 as a private rollback
   copy; install only the signed build 9 candidate at the same app path. Register
   only its existing URL scheme as normal for Companion, with no DNS, firewall,
   Authentik, OpenBao, gateway or broker change.
3. Launch build 9 once with `--aster-local-codex-pilot`. The button is otherwise
   hidden. Jason reviews the **exact fixed Orion fictional question** in the
   pilot screen, checks explicit ChatGPT cloud consent and clicks Send once.
   No personal context, chat history, credentials, incident data or tools are
   included. The app records only the request ID before launching the helper.
4. The signed app runs its bundled Python helper as a one-shot child over private
   stdin/stdout pipes. The helper rechecks the exact manifest, uses the existing
   local ChatGPT-signed-in Codex App Server, attempts at most one model turn, and
   exits. Its journal is under an owner-only Companion Application Support
   directory; it stores thread/turn IDs and state, not prompt or answer text.
5. Validate Jason saw the final answer, one request ID maps to one Codex turn,
   the gateway job count did not grow, worker identity remained inactive, no
   worker token or paid API-key fallback was used, and normal Companion login
   and household/local paths still work. Record elapsed time, manual steps,
   preflight duration, tool/approval requests (expected zero), failure class,
   and any Mac sleep/restart effects. Do not repeat a failed or uncertain turn.
6. Close the pilot app. Unless normal use is separately accepted, relaunch
   Companion without the pilot flag, leaving the pilot control hidden. Preserve
   the journal as reconciliation evidence. Restore build 8 if login, normal
   functions or signature behavior regresses.

## Stop conditions and recovery

Stop before Send on a manifest mismatch, unverified signature, changed installed
baseline, account/configuration uncertainty, missing rollback copy or unexpected
credential prompt. After Send, a timeout, app crash, tool/approval request,
unknown result or provider error is **not** proof of cancellation. Keep the
request ID and journal, inspect the known Codex thread/turn read-only, and do
not create a second turn without a separate reconciliation decision. An answer
is volatile in Companion; Jason can copy it from the screen if he wants to
keep it. Installing the candidate does not activate the gateway worker.

Rollback is app-local: quit build 9, restore the verified build 8 bundle and
its Launch Services registration, confirm signature/login/normal interface,
and leave the local journal untouched for audit. No production gateway setting
needs changing. A successful one-turn trial is evidence only for the native
no-tools path and cannot authorize general questions, automatic routing,
sysadmin tools, standing background execution or high-impact action.

## Approval boundary

Local code, tests, signing and metadata checks were within Stream A. The
specific **installed app replacement and one subscription-backed model turn**
are the next connected risk gate. They require Jason's explicit approval of
this bounded action. A Git push is separately subject to the repository's
immediate per-push confirmation rule.

## Bounded live result — 2026-10-08

Jason approved the exact app-replacement and one-question gate. Before the
replacement, the installed build 8 and signed build 9 executable hashes matched
the pinned values above. The bundled metadata-only Codex preflight matched the
pinned manifest: ChatGPT authentication, `gpt-5.6-luna` at medium effort, no MCP
servers, read-only sandbox and web disabled. The default sandbox invocation
could not connect to the local App Server; the platform-reviewed preflight
completed without starting inference. Aster was active and healthy, with 44
paths and no POST job-intake route. The gateway ledger contained two jobs. The
existing Authentik worker was inactive, with zero unrevoked access or refresh
grants for its provider.

The running Companion process was stopped. A fresh complete build 8 rollback
copy at `/Applications/AsterCompanion.pre-local-bridge-20261008.app` passed
signature verification and the pinned executable hash. The original installed
bundle was also moved aside as
`/Applications/AsterCompanion.pre-local-bridge-staged-20261008.app`. Only the
signed build 9 was installed and registered at the normal app path; its
installed executable hash and signature passed verification. Companion was
launched with the explicit pilot flag.

Jason reviewed the fixed fictional Orion question, checked cloud consent and
clicked Send exactly once. Companion visibly reported one completed local Codex
turn and displayed a final answer. The answer distinguished the observed 503
and later 200 from unknown cause and user impact, and recommended read-only
checks without claiming any had been performed. The private local journal had
one completed job, one thread ID and one turn ID, with a usage record. Its jobs
schema holds IDs, state and owner, not prompt or answer text. The owner-only
state directory and files had modes 0700 and 0600 respectively. No answer text
or credential was copied into the repository.

Immediately afterward, the gateway still had two jobs; Aster still exposed 44
paths and only GET on the owner jobs collection. The worker remained inactive
with zero unrevoked access/refresh grants. The observed path required one app
launch, one review/consent and one Send click, with no worker activation or
gateway request admission. Elapsed request time and Mac sleep/restart behavior
were not measured in this trial; do not infer reliability from one success.
Normal-use closeout and app relaunch without the pilot flag remain pending until
Jason has had the chance to copy the volatile answer privately.
