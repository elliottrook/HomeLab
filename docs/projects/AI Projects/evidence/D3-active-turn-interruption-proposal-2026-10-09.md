# D3 next gate — one active-turn process-interruption experiment

**Status: local proposal; no live request or interruption authorized by this
document.** Owner: Jason. The [prior gate](D3-native-live-reliability-gate-2026-10-09.md)
proved one reviewed native send, a short sleep/wake and read-only recovery of
the completed original answer. The Vega turn finished before interruption.
Do not resend Vega or describe active-turn recovery as passed.

## Hypothesis and limits

For one new, explicitly reviewed fictional question, if Companion exits after
the dispatch journal durably records a Codex turn ID, reopening the same
signed app will expose either the original completed answer or an honest
unresolved state without starting a second turn. This tests the local
handoff/reconciliation path, not sysadmin skill, routine release, a hard crash,
natural credential refresh or model routing.

The proposed exact question is:

> In a fictional home lab, the media indexer Nova returns HTTP 502 while its
> health endpoint returns 200. No logs, metrics or network checks have been
> run. Give a 12-row table of plausible failure points, one read-only
> observation that would distinguish each, and one fact that would falsify
> each. Then give a short triage order. Do not claim to have inspected,
> repaired or changed anything.

It contains no real home-lab details or personal context. The longer response
format may increase the chance of observing a running turn, but is not a
guarantee; if the turn completes first, record an inconclusive interruption
test and do not send a replacement to chase a pass.

## Local-only trigger preparation

The one-shot watcher is
[`active_turn_interrupt.py`](../../../../apps/AsterCompanion/Experiments/active_turn_interrupt.py).
It is outside the Companion bundle and cannot start a model request. It reads
only the owner-only, content-free `manual-pending.json` and `jobs.sqlite`,
requires the exact installed executable SHA-256 and one flagged Companion PID,
and defaults to a no-signal dry run. `--arm` is required to send SIGTERM. It
signals only the exact PID after a **new** request has state `running` and a
recorded turn ID. A completed turn, pre-existing pending ID, unexpected extra
job, changed executable/process, uncertain state or timeout results in no
signal. The watcher prints metadata only. Five offline tests cover eligible,
ineligible, dry-run and exact-PID behavior. A no-arm preflight against the
current saved Vega ID aborted without signalling, as intended. This code is
not installed in Aster or running in the background.

## Proposed one-attempt sequence

1. Reconfirm version 15 signature/executable hash, one signed-in app process,
   normal Aster and AI-PAM, journal exactly 14 completed rows, and the
   version-13 rollback bundle. Verify the pinned ChatGPT account/model,
   read-only sandbox, disabled web and zero MCP tools by metadata-only
   preflight. Do not inspect token values or historical answer text.
2. Jason confirms the prior Vega answer is saved. In the native manual view,
   recover that completed ID if needed and click its explicit acknowledgment
   once to clear the completed-only guard. Confirm no new turn was started and
   the manual pending record is absent. Do not delete it through Finder or a
   shell command.
3. Display the exact Nova question for Jason's review and per-request ChatGPT
   consent. Before his one Send click, start the watcher for the exact flagged
   PID with a 45-second limit and `--arm`. This is a supervised, local
   process-control experiment; the watcher does not read the question or
   answer.
4. If the watcher reports `signalled_on_observed_running`, verify only
   Companion exited. Reopen the same signed bundle with the manual flag and
   inspect **the same saved request ID**. Use only the UI's recovery or
   reconciliation action for its recorded turn. If the result is unknown,
   preserve it and stop; never clear or resubmit the ID. If the watcher
   reports another outcome, do not interrupt after completion or retry.
5. Quit manual mode and reopen ordinary Companion without the flag. Check
   sign-in, AI-PAM approvals, hidden manual send, journal state and any
   Keychain prompt. Restore signed version 13 only if normal Aster regresses;
   preserve the journal and Codex IDs.

## Acceptance, stop and authority

One new request ID maps to at most one Codex turn; no unreviewed cloud send,
tool/approval item, credential exposure or infrastructure access occurs; the
post-interruption state is truthful (`completed` from the same turn or
`unknown`), with no automatic retry; normal Aster remains usable. Record
whether SIGTERM actually preceded completion, the exact journal transitions,
turn count, user-visible recovery result, prompt count and any rollback.
One pass is only a narrow process-interruption observation, not a reliability
rate or a hard-crash result. A duplicate, unexpected tool request, secret
exposure, wrong PID, unexplained journal mismatch or broken ordinary Aster
stops the experiment.

The proposal requires separate owner approval immediately before the new
ChatGPT turn and deliberate app interruption, plus Jason's in-app review and
consent. No gateway/worker activation, AI-PAM grant, infrastructure mutation,
Keychain ACL change, Mac sleep or Git push is part of this experiment.
