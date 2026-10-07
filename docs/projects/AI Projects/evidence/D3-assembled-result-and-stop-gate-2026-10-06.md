# D3 assembled worker result and real-stop approval gate

## Approved one-turn run — complete

Jason approved the exact `ca2c38ade77e4fc221b6bfcf73aad06b81cda623724e1cf6da2bb19fa1d3728c`
manifest. Ran once from commit `eb9041e`, with existing ChatGPT authentication,
`gpt-5.6-luna` and medium reasoning. The assembled worker completed in 5.311
seconds, including its local HTTP handoff/result path, excluding metadata
preflight. This is one observation, not a latency distribution or SLO.

[Retained result](D3-assembled-result-2026-10-06.json) confirms an owner-visible
final answer and reported token usage. The answer correctly separates the two
given HTTP observations from unknown cause, duration, user impact and current
service health, and proposes read-only checks without claiming real inspection.

A fresh restricted app-server connection performed only `thread/read` on the
known turn. [Verification](D3-assembled-recovery-2026-10-06.json) confirmed one
dispatch record, one completed provider turn, one final answer and an exact match
to the owner HTTP response. Item types were userMessage, reasoning and
agentMessage; no tool activity was recorded. No hidden reasoning was copied into
the retained evidence. Final-answer SHA-256:
`3d77f8d934dfe41bf7dcb3f03631065cf9cec9519d0f19031278b5ce701bd34c`.

Provider-reported usage: 7,888 input tokens (4,864 cached), 192 output tokens,
32 reasoning-output tokens and 8,080 total tokens. Preserve these field meanings;
do not add reasoning tokens again to the provider's total. They are not a dollar
charge or a measure of remaining subscription allowance. The modest fictional
prompt still incurred substantial context; the result does not establish that
Codex is a lightweight choice for household commands. Keep those deterministic
or qualified local tasks. Context provenance/efficiency needs separate measured
analysis rather than guessing which instruction layer accounts for the count.

Both gateway and owner identity were **local test fixtures**. This proves the
assembled worker can use the real subscribed Codex agent and deliver its result
through the candidate HTTP route logic. It does not prove production Companion
deployment, private-lab data routing or general sysadmin correctness. No new
identity, persistent service, infrastructure mutation or Git push occurred.

The approval is consumed. The historical code/manifest are retained. Do not
rerun it after later source edits.

## Local continuation

Prepared one bounded stop mode in the same pilot. After Codex acknowledges the
turn and the worker sends its running receipt, the test owner requests stop
through the Companion cancellation route. The normal worker poll must observe
that request and send a correlated `turn/interrupt`. Only a provider terminal
`interrupted` event counts as confirmation; a stop request or RPC acknowledgement
alone does not. A local fixture verifies that sequence and suppresses final text.

141 Python tests and five renderer scenarios pass. The stop mode has only been
fixture-tested, not run against a real model. Both identity tests are complete;
no additional authentication-only experiment is proposed.

## Exact next approval — one real stop test

Approve one fictional Orion turn, same model, medium reasoning and subscribed
authentication, with stop requested immediately after the running acknowledgement.
No tools, private lab context, API-key fallback, automatic retry or deployment.

[Prepared manifest](D3-cancel-manifest-2026-10-06.json) fingerprint:
`7fcad97583ef0092c76de9c101b9182d7eff7fb8cb47fee407c8b5b1362182c3`

```text
/private/tmp/aster-delegation-gateway-py311-20261006/bin/python services/aster-agent/delegation/assembled_pilot.py --cancel-after-ack --run --approved-sha256 7fcad97583ef0092c76de9c101b9182d7eff7fb8cb47fee407c8b5b1362182c3 --output-dir /private/tmp/aster-d3-stop-orion-20261006
```

Expected seconds, with the same 180-second overall execution target, five-second
stop grace and bounded RPC/network calls described in the previous gate. The
process owner closes its app-server and retains records on exit. That closure
alone must never be reported as confirmed provider interruption. The output
directory must be new, and fingerprint mismatch refuses dispatch.

Success: exactly one turn; stop requested through the owner route; corresponding
provider interruption confirmed; no final answer exposed; no duplicate dispatch.
Read the saved turn afterward without new inference. If the answer completes
before interruption, record that race as **inconclusive for live cancellation**,
not successful cancellation, and do not automatically run another turn. Timeout
or lost acknowledgement stays unknown and requires reconciliation. Preserve the
result regardless of success; never change the acceptance test to match it.

This is a new cloud call, so the governing project's connected-test approval
rule applies. Previous one-turn approval does not transfer. All local preparation
for this exact stop test is complete; await approval here.

## Resume after the stop gate

No general sysadmin promotion follows. Continue permanent worker custody,
AI-PAM kill-switch integration, scoped deployment/rollback and native Companion
wiring. Permanent vault policies/roles, credential issuance, live service changes
and real lab-context egress retain separate explicit boundaries. Do not bypass
human-held vault administration or reuse the Forgejo service identities merely
to make deployment easier.
