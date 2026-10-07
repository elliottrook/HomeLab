# D3 — Assembled finite worker and one-turn approval gate

## Implemented and verified locally

`worker.py` now joins the existing gateway, admission ledger, Session, pipe
adapter and final-answer/usage paths for one explicitly assigned job. It is
disabled by default and has no queue enumeration or automatic retry. Stop state
is checked before and after thread creation, before turn submission, and during
the event loop. A pre-dispatch stop sends no inference and leaves a reviewable
unknown handoff rather than inventing a provider interruption. A confirmed
provider terminal event alone establishes completed/failed/interrupted.

Lost control connectivity causes a best-effort interrupt and an unknown outcome;
it does not prove remote compute stopped. A missing initial acknowledgement is
never guessed. Lost final delivery retains the completed worker record and
gateway digest for recovery. The owner of the app-server process closes it in
`finally`. The worker cannot create a second turn after an uncertain admission.

140 Python tests plus five renderer scenarios pass, including the assembled
pilot's HTTP owner-result path, private state-file modes, exclusive output
directory, stop before execution, stop while running, lost start acknowledgement,
control outage, deadline expiry and lost answer delivery. Fixtures are not live
evidence. No running Aster service or permanent credential was changed.

## Metadata-only installed preflight

Prepared the [manifest](D3-assembled-manifest-2026-10-06.json) without starting a
thread or turn. ChatGPT authentication, native OpenAI provider, local configured
model `gpt-5.6-luna`, medium reasoning, read-only sandbox, zero enabled MCP
servers and the existing disabled-tool configuration passed the same pilot
checks. The CLI reports `0.159.0`; the executable hash is retained in the manifest.
An initial sandboxed app-server failed to initialise; the platform-authorised
metadata-only run succeeded. This was not a model failure or cloud attempt.

This model choice is an integration baseline, not a sysadmin qualification or
decision to use it for all infrastructure reasoning.

## Exact next approval

Approve one fictional Orion request through the assembled worker, using the
existing ChatGPT subscription sign-in. Maximum one model turn, no tools, no API
key/fallback, no retry. Model and reasoning are the preflight values above.
The exact prompt is retained in the manifest and asks what can be concluded
from a fictional HTTP 503 followed by HTTP 200, with no invented investigation.
No real lab evidence, personal content or credentials are included in the prompt.

The gateway and owner identities in this run are explicitly **in-process test
fixtures**. It exercises the real worker and Codex pipe, with HTTP route logic
for handoff and owner result delivery. It does not deploy the gateway, use a
production worker token, send traffic to Aster, or prove the native Companion
display. Real Mac-to-Authentik issuance/revocation was separately proved already.

Reviewed combined manifest SHA-256:

`ca2c38ade77e4fc221b6bfcf73aad06b81cda623724e1cf6da2bb19fa1d3728c`

```text
/private/tmp/aster-delegation-gateway-py311-20261006/bin/python services/aster-agent/delegation/assembled_pilot.py --run --approved-sha256 ca2c38ade77e4fc221b6bfcf73aad06b81cda623724e1cf6da2bb19fa1d3728c --output-dir /private/tmp/aster-d3-assembled-orion-20261006
```

The fingerprint includes every local Python module and the installed executable,
model, configuration and prompt. A mismatch refuses execution. The output
directory must be new; no existing results are overwritten. The run retains a
manifest, private SQLite state and final-answer/status evidence. Codex retains
its fictional conversation for subsequent read-only reconciliation.

Expected seconds to a few minutes. Execution deadline 180 seconds from worker
start, with a five-second interruption grace and bounded individual RPC/network
calls; this is not an absolute three-minute process-wall-time guarantee. On
failure, stop the owned app-server, retain uncertainty and inspect existing
records. Never resubmit automatically or treat closing the local process as
proof the provider stopped. No production rollback is needed because nothing
is installed; retain evidence and leave the candidate disabled.

## Acceptance

- One durable worker claim, one correlated turn, no tool/server-request execution.
- Completed final answer matches what the owner HTTP route returns, without
  rewriting. The answer distinguishes given evidence from unknowns.
- Numeric usage is either provider-reported or explicitly unknown; unknown
  remains an outstanding telemetry limitation, not estimated usage.
- No automatic retry, paid API fallback, production mutation or permanent
  credential. Any unexpected scope change stops the test.

This is a connectivity/lifecycle experiment, not a benchmark or permission
promotion. Actual live cancellation is still separate from fixture evidence.

## Why approval is required / resume

The governing project requires a concrete approval for each connected cloud
test. The previous approvals covered other consumed tests, not this new model
turn. The implementation, local fault tests and metadata preparation for this
step are complete. Await this specific approval, run once, retain the result,
then continue actual deployment and credential-custody preparation.

Permanent OpenBao setup is not silently bypassed to run this test. It creates no
new long-lived credential and grants no target access. Production needs the
AI-PAM registry, global kill-switch binding, supported vault administration,
worker custody/rotation/revocation, deployment checks and a separately reviewed
change. Those remain open; the new runner is not yet a household background
service or a working deployed Aster-to-Codex interface.
