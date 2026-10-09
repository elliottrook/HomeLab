# D3 — signed build 10 first-case gate

**Status: PREPARED LOCALLY; NOT APPROVED OR EXECUTED.** Owner: Jason. This is
one explicitly reviewed fictional question to check the new finite-evaluation
path, not approval for the remaining eleven, arbitrary prompts or sysadmin work.

## Why this gate exists

The [build 9 one-question trial](D3-native-local-bridge-gate-2026-10-08.md)
proved the simplest native connection works once. It did not test moving from
one question to another, recording latency or handling a restart with an
existing request. The [12-case preregistration](D3-native-normal-use-preregistration-2026-10-09.md)
keeps these questions fictional and fixed. This gate tests only case 1 and
its content-free measurement path before considering more turns.

## Frozen baseline and candidate

- Installed `/Applications/AsterCompanion.app` remains signed build **9**, with
  executable SHA-256
  `a284b7d2525698c982736d94baa624115dbce3fe72d275fd53dec0567beeddd2`.
  Its normal signed-in Aster view was verified after a macOS Keychain prompt.
  The completed fixed-pilot local journal has one request and one turn.
- Signed, unregistered build **10** is local at
  `apps/AsterCompanion/.build/out/Products/Debug/AsterCompanion.app`; executable
  SHA-256
  `d7c9c98faa79cfa57b01ebcd2b05eebcee0c51776c05b0527791450a2ee76516`.
  Strict signature verification passed. Its hidden evaluation UI source SHA-256
  is `40a7c150bea473aee6a520757bb79e180cf401b9f98beae0b08c3238305c7bc8`.
- The bundled metadata-only manifest SHA-256 is
  `6063d71daf8ee917dcb95e5e6836d0bbdfd768df88870b14922da2b091ce285b`:
  ChatGPT sign-in, `gpt-5.6-luna` medium, zero MCP servers, read-only sandbox,
  web disabled, one turn and no inference during preflight. No paid API key,
  gateway worker token or infrastructure tool is included.
- Local results: **297 Python tests** and **46 native tests** pass. They include
  fake Codex one-turn/duplicate refusal, owner-bound read-only status, private
  content-free logging and symlink refusal. No build 10 model turn has run.
- At the last live check, Aster was healthy with 44 paths, no owner POST job
  intake, two historical gateway jobs and an inactive worker with zero
  unrevoked grants. Recheck these immediately before any deployment.
- The evaluation AppStorage keys did not exist at preflight. Require no
  preexisting pending evaluation ID and starting index zero immediately before
  the trial; do not reset or erase unexpected state.

## Exact action proposed

1. Recheck all hashes, signature, manifest, gateway closure, worker inactivity,
   installed app state and empty evaluation keys. Preserve a fresh, verified
   whole-build-9 rollback copy without replacing earlier backups. Stop on drift.
2. Quit Companion, install only signed build 10 at its existing app path and
   register its existing URL scheme. Launch it with
   `--aster-local-codex-evaluation`. No DNS, firewall, Authentik, OpenBao,
   broker, gateway or cloud-account changes.
3. Jason reviews **case 1 only**: “What does HTTP status 503 mean? Answer
   briefly and distinguish it from proof of a lasting outage.” He checks the
   explicit ChatGPT cloud-consent box and clicks Send once. No personal data,
   logs, credentials, system context or tools are sent. Do not click the
   next-question control in this gate.
4. Verify one completed local request maps to one Codex turn; the answer is
   visible and does not infer a lasting outage; the owner-only metadata log
   records submitted/completed, case index 0, manifest and timings but no
   question or answer; the gateway remains at two jobs and the worker stays
   inactive. Record end-to-end latency, one-turn latency, Keychain prompt count,
   any tool/approval event, failure class and the frozen rubric result. Jason
   is not the technical correctness backstop. No
   automatic retry after an uncertain result.
5. Jason has the chance to copy the volatile answer privately. Close the
   flagged app and reopen Companion without the flag. Verify signed-in normal
   Aster UI, pilot control hidden and request intake still closed. If normal
   login or function regresses, restore verified build 9 and retain journals.

## Stop, rollback and decision

Stop before Send if the account, manifest, signature, prior journal, worker or
gateway differs from the frozen baseline; if a credential prompt is unexpected;
or if the reviewed question is not exact. After Send, timeout, crash or helper
error is an **uncertain** turn until the original thread/turn is reconciled
read-only. Do not create a replacement ID or repeat the question. A tool or
approval request stops the test and requires separate investigation. A single
successful case advances only to review of the remaining finite set, not a
routine-use claim. Preserve the private journal and the old signed app bundle.

This gate requires Jason's explicit approval immediately before installing
build 10 and sending the one subscription-backed question. Git push is a
separate per-operation approval under `AGENTS.md`.
