# Subscription delegation: D0/D1 evidence — 2026-10-06

## Verified current state

Installed CLI: `codex-cli 0.158.0-alpha.2.1`. Local stdio app-server accepts
`initialize`, `account/read` with `refreshToken:false`, and `model/list`.
The dedicated metadata probe returned:

```json
{"status":"metadata_ok","auth_mode":"chatgpt","model_count":6,"more_models":false,"inference":false,"entitlement_proven":false}
```

The first sandboxed attempt disconnected during initialization. Repeating the
same metadata-only probe with approved host runtime access succeeded. This is
not an inference result. No thread, model turn, new login, credential copy,
production deployment or Git push was performed.

The CLI-generated protocol describes `agentMessage` with `id`, `text` and
optional nullable `phase`. The candidate accepts only explicit `final_answer`;
unknown phase causes missing-final abstention. `turn/completed` must independently
report success. Model catalogue membership does not establish available quota.

Generated schema SHA-256 values (reproduce with this exact CLI version and
`codex app-server generate-json-schema --out <temporary-directory>`):

| v2 schema | SHA-256 |
|---|---|
| ItemCompletedNotification.json | d04b9153de38cd8302a2a418a44a65e8265d4c7586d46ea2cc801b594c6acf5b |
| ThreadStartParams.json | e9c6d3cc18d049bfbc0249add3808fb8e5a27e1a0b5a423767aafbc3859a9428 |
| TurnStartParams.json | 2dfcf68705896fadc344ccfeb2e9fe5a6bcbbb8b9a90cf449ce232b636daf05a |
| TurnCompletedNotification.json | 20052f79e907069a0d7948b93ba0927fa08f9a2faac23a63a0e8e527ae6bf0f7 |

## Local candidate and acceptance limits

18 standard-library unit tests pass. Tests exercise local fast routes, privacy
and auth rejection, capacity unavailable, unknown intent, correlated final
answers, failed/interrupted turns, unknown phase, blank answers, duplicate and
conflicting messages, output cap, cancellation uncertainty and rejection of
server requests. SQLite tests cover claims surviving restart, two connections
claiming one job, immutable binding and matching terminal events.

This is initial D1 evidence, not D1 completion. No free-text router, integrated
durable job transport, quota-specific event handling or live cancellation has
been proved. Rejecting approval requests is not proof of internal tool isolation.
The installed feature listing includes enabled shell, apps, plugins, browser and
multi-agent capabilities; launching a default child must not be assumed isolated.

## D2 preregistration — proposal, not an executable release

Hypothesis: a separately scoped Codex session using existing ChatGPT sign-in can
return a usable answer through the Aster adapter without API billing or access to
HomeLab. This tests integration, not sysadmin superiority or production readiness.

Fixed fictional input:

> Fictional exercise only. Service Orion returned HTTP 503 once. A later health
> check returned HTTP 200. No logs, dependency checks or user-path checks have
> been performed. Explain what is known, what remains unknown, and the next
> read-only checks. Do not claim you inspected or repaired anything. Use only
> this supplied information. Do not use tools.

One turn, one dedicated job/thread, existing Mac, empty temporary working area,
ChatGPT authentication only. Model must be explicitly recorded from the installed
catalogue before approval; no silent model or billing fallback. Proposed watchdog:
180 seconds, then interrupt and reconcile; disconnection or timeout never means
the model stopped. No automatic retry. Subscription token use is expected even
though no API-key billing is intended.

Before execution, the candidate must establish effective tool denial (including
internal shell, web, MCP, apps and delegated agents), no inherited repository or
personal context, supported authentication, bounded transport and job recovery.
Prompt text saying “do not use tools” is not this control. The precise installed
configuration and a tested runner remain outstanding; do not request blanket
permission in place of this engineering work.

Record only job/thread/turn identifiers locally, version/config fingerprints,
selected model, authentication class, elapsed time, reported token counts, final
answer and terminal status. No credentials or hidden reasoning. Keep fictional
fixture and sanitized result in Git; normal provider retention applies to the
submitted fixture. Failure leaves live Aster unchanged; stop the owned bridge
process only after handling any uncertain remote turn.

Pass requires a matching terminal success, nonempty faithful final answer, no
tool activity, no unsupported claim of real inspection, and the expected
subscription route. Review failures before another attempt. After preparing the
runner and proving isolation, resolve any remaining connected-test authorization
against Jason's adopted scope and existing project gates. Approval cannot make an
unverified isolation claim true.

## Sources and provenance

Architecture rationale and official auth/app-server references are in
[Codex delegation](../Codex-Delegation.md). Installed CLI schema and feature
inspection take precedence over assuming a public example matches this build.
The [official harness explanation](https://openai.com/index/unlocking-the-codex-harness/)
describes the distinction between threads, turns, streamed items and agent tools.
All results above concern the new local candidate, not the running Aster service.
