# D2 bounded subscription pilot — ready for connected-test approval

## Evidence completed

50 offline tests pass. Added bounded sequential JSON-RPC over pipes, notification
delivery before RPC acknowledgement, read/write timeouts, server-request refusal,
and full-snapshot recovery of a known turn after restart. Persist the thread ID
before dispatch, even when the turn acknowledgement is lost. Unknown dispatch
never triggers automatic replay. Tests cover quota/auth classes and manifest
rejection for wrong authentication, unavailable models or custom endpoints.

An offline loopback HTTP provider captured the actual outgoing Codex request:
zero offered tools and no Authorization header. It returned an intentional HTTP
400, so there was no model answer or real provider inference. The repository copy
reproduced that result. This used the installed model selection and restriction
profile; a fake provider is not evidence that ChatGPT inference works. It is
bounded tool-offer evidence, not a security certification or OS isolation claim.

Generated experimental schemas were inspected; no general tool-inventory RPC
was found in that generated surface. Hence the actual outgoing-request capture
was used instead of treating configuration flags as sufficient evidence.

## Exact proposed operation

On the existing Mac, launch one owned app-server child with the pinned restriction
profile. Use existing ChatGPT authentication, native OpenAI provider and the
installed configured `gpt-5.6-luna` model with **medium reasoning**. This tests
plumbing, not whether that model should perform HomeLab sysadmin work. No paid
API fallback or model substitution. A dedicated temporary empty working area
supplies no HomeLab repository documents or tools. Existing supported Codex auth
remains in its normal custody; no credential copy.

Send only the fictional Orion request in
[the prepared manifest](D2-prepared-manifest-2026-10-06.json). One turn; 180-second
watchdog, then a bounded interrupt attempt. Adapter does not retry. Native Codex
may retry provider connections within that turn; “one turn” is not a promise of
one HTTP request. Disconnection/timeout is recorded unknown, never as stopped.

Proposed command from this worktree (do not execute before approval):

```sh
python3 services/aster-agent/delegation/pilot.py --run \
  --manifest-sha256 6a8a916165d50bb35f779face26c5705dc147961bdf42f14e88297c827679d12 \
  --output-dir /private/tmp/aster-d2-orion-20261006
```

The manifest pins source files, Codex executable hash, model, reasoning setting,
fixture and restrictions. Changed metadata/code makes dispatch fail. Output
directory must be new. Results and identifiers remain local. Codex stores its
dedicated thread using its usual mechanism so later read-only reconciliation is
possible. Standard provider handling applies to the fictional prompt.

Pass: subscription authentication, matching terminal success, nonempty faithful
final answer and no unsupported assertion of real inspection or repair. Inspect
the returned answer, not only the exit status. Report elapsed time. Token usage
collection is not implemented in this initial runner and must be reported UNKNOWN,
not zero. This bounded connectivity pass does not complete the original D2 usage
observability acceptance criterion or qualify production delegation.

Recovery: leave production Aster unchanged; close only the owned child. Preserve
job/thread/turn records. Read the dedicated thread before any retry if its state
is unknown. A lost turn acknowledgement is deliberately a manual-reconciliation
case. Successful cancellation and reconnection still require connected evidence.

## Why approval is requested here

The canonical programme's 2026-09-28 amendment says “cloud egress ... retain
their stated risk and authorization gates.” The October 6 amendment retained
concrete connected-pilot gates. Local engineering and metadata inspection needed
no new approval; this next operation sends a prompt to the cloud and consumes
subscription capacity. Approval is for this exact fictional test, not production
access, automatic sysadmin actions or Git publication. No approval-review tool
rejection occurred during preparation.
