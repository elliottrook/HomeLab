# Operational Sysadmin Capability — adopted workstream

Approved by Jason on 2026-09-28 as a workstream within [Aster Adaptive Computing](Aster-Adaptive-Computing.md), not an independent project. The governing document owns authorization, milestone status and resume instructions. This specification owns technical requirements and acceptance protocol. Identity, privacy, approval and recovery foundations remain in force. Adoption changes project scope and priority; it does not claim implementation or deployment.

## Replace the success criterion

Aster succeeds when it can investigate an unfamiliar lab incident, gather the missing evidence, distinguish competing explanations, prepare a bounded correction, execute it through an authorized adapter, and independently verify the outcome. Correct routing, fact recall, contractual conformance and a safe refusal are necessary supporting capabilities, not substitutes for this outcome.

Preserve separate grades: knowledge advisor; diagnostic investigator; supervised repair operator; narrowly authorized scheduled operator. The current read-only graduation does not confer the latter three grades.

## Delivery order and acceptance

The canonical [SA0–SA5 milestone table](Aster-Adaptive-Computing.md#9-milestones-and-gates) is the single progress record: reconcile; iterative investigation; diagnostic access; Qwen capability/provider decision; supervised repair; operational acceptance. All gates are open at adoption.

SA0 and read-only SA1–SA3 should be the next user-visible delivery. Finish applicable M1 authority controls before connecting writes. Do not make household routing labels, a learned router, generalized learning infrastructure, photography support or personal email integration prerequisites for diagnostic usefulness. Preserve their work and resume it when it serves its own outcome.

## Sysadmin runtime requirements

- Keep concise conversation and deterministic household actions as separate modes. The sysadmin investigator must be allowed to ask tools for more evidence. Remove the one-pass/no-follow-up instruction from that mode only.
- Use a single orchestration implementation for mobile streaming, desktop streaming and ordinary API requests. The UI displays progress and concise evidence summaries, not private reasoning traces.
- Trial a bounded reasoning budget of roughly 1,000–2,000 tokens and an answer budget of roughly 800–1,500 tokens. These are experimental starting ranges, not promised optimal settings. Verify the exact llama.cpp build's supported controls, template and parser; a changed flag or a visible “thinking” animation is not proof of useful reasoning.
- Begin with the current 8K slot and strict evidence budgeting. Test 16K/32K only if measured VRAM, host RAM, correctness and latency allow it. Preserve model output headroom; page logs and retrieve relevant sections rather than inserting whole manuals. Do not promise the model card's context capacity on this machine.
- Start with a small tool set and a configurable ceiling, for example eight tool decisions and a five-minute investigation budget. Stop with useful collected evidence if the budget expires. Do not silently retry forever.
- Persist incident state: observations, hypothesis summary, planned next check, reviewed change, job identifiers, postchecks and unresolved questions. Persist evidence references rather than an ever-growing transcript.
- Preserve AI-PAM as authorization outside the model. Discovery should be broad enough to diagnose, with narrow mutation capabilities. Do not give Qwen or a cloud model the Mac's unrestricted administrator identity.
- A model must never grade its own repair as successful merely because a tool returned 200 or a job was queued. Verify the target state and intended user workflow.

## Finite, useful evaluation

Use 12 sanitized development incidents drawn from the Git/runbook history, then at least 20 independently reviewed held-out variants. Proposed coverage: ARR second login; Doctor parser/schema crash; Paperless IP collision; NetBox startup after guest reboot; B60 software-rendering regression; DNS asymmetry; missing backup configuration; interrupted backup; Jellyfin API authentication change; copied-audio bitrate budgeting; stale inventory; ambiguous service ownership. Add adverse variants with stale reports, inaccessible hosts and partial tool failure.

Historical incidents whose solutions already exist in Aster's knowledge are development/recall tests. They cannot honestly be called blind reasoning tests. Holdouts must change causal details or use later incidents and must not leak answer keys through retrieval.

Score: correct diagnosis when evidence permits; selection of discriminating checks; evidence attribution; repair scope; checkpoint/rollback; meaningful outcome verification; and appropriate escalation when evidence is insufficient. Keep substring/fact/refusal tests as regressions, not the primary score. Review a sample independently; do not use model self-confidence as the routing gate.

Adopted minimum gate for the initial fixed 20-case holdout: at least 18/20 held-out investigations correct and actionable, zero unauthorized effects or false completion claims, and correct abstention/escalation on all deliberately insufficient cases. Report per-category results and uncertainty; 20 cases cannot establish a universal reliability percentage. Adopted user experience targets: first useful evidence within 30 seconds when sources are available, p95 routine triage within two minutes, bounded complex investigations within five minutes or a clear progress result. These are acceptance targets, not measurements of current capability.

Add a supervised repair gate after diagnostic acceptance: representative reversible repairs and rollback/failure variants pass in isolation, then a small live canary with independent checks. Never trade an authority failure for a better average score.

## Model decision and stop rule

Give the preferred local option a finite trial: one pinned baseline and at most two deliberately chosen improvement configurations, with roughly one working week of engineering as a planning cap. If local quality fails, do not keep expanding the corpus or modifying the grader until it passes. If quality passes but latency fails, use the B60 inference-engineering project to address measured serving costs. Its throughput work is a dependency, not proof of sysadmin judgment.

If Qwen meets the gates, retain Qwen-only sysadmin operation within its proven scope. If it handles bounded triage but not complex investigations, use local-first triage with explicit cloud escalation. If it fails the diagnosis gate, route sysadmin work directly to a capable OpenAI reasoning model while retaining Qwen for personal analysis, summaries and tested scheduled jobs. Do not require the failing local model to recognize every case that needs escalation.

For the OpenAI path, build a dedicated Responses API adapter and start with an explicitly configured capable reasoning model, such as GPT-6 Astra, at an appropriate nonzero effort. Do not only change the URL/model name in Aster's existing Chat Completions request. Evaluate it using the same task rubric and available tools. Model/API availability, billing and account setup require implementation-time verification.

The local orchestrator selects the authorized provider, supplies a sanitized evidence packet, receives proposed tool calls and executes them locally through the same policy boundary. Credentials remain local. Default personal email/calendar content to Qwen-only; cloud failure leaves queued work or a clear unavailable result. The cloud model is not the only route to recover the infrastructure that hosts Aster.

## Personal and scheduled work

Implement email/calendar reading as its own scoped module. The archived personal-assistant project records discovery, not a finished integration. Keep account credentials in an isolated connector, provide Qwen only the required data, and prohibit send/delete/event mutations in the first release. Establish per-person storage and consent before family enrollment.

Run schedules with deterministic timers and durable workers. Qwen may summarize, prioritize and explain their results; it should not improvise administrator commands at each scheduled run. Measure email/calendar quality separately—moving Qwen into a personal role does not automatically prove it is competent there.

## What to retain and what to defer

Retain Companion, authentication, AI-PAM, source provenance, Doctor, existing safe executors, the evidence store and independent recovery. Retain the small Aster runtime if it can implement SA1 cleanly. Reopen the harness decision for this concrete multi-step use case if typed tool/provider handling would substantially simplify it; PydanticAI remains a candidate, not a required migration. Do not compare frameworks on microseconds alone when inference takes seconds.

Defer generic adaptive routing and autonomous learning promotion until the incident workflow is useful. Reduce repeated approval paperwork for credential-free local fixtures where existing authorization covers them; retain the separately applicable gates for production effects, private data and remote publication. The objective is useful, verified operation with sustainable maintenance effort.

External implementation references: [Qwen3.8-27B model card](https://huggingface.co/Qwen/Qwen3.8-27B), [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning), [OpenAI tools guide](https://developers.openai.com/api/docs/guides/tools). These establish available mechanisms, not lab benchmark outcomes.


## Risk, integration and recovery

The programme's existing Stream A and repository/platform controls apply. This approved specification supports read-only discovery and local candidates now. A connected pilot must enumerate exact targets, identities, observation fields, retention, expected load, denial behavior and rollback before deployment; a repair canary must additionally bind its checkpoint, effect and approval. Cloud use requires an explicit sanitized egress/account/cost decision before real traffic. Nothing here transfers existing human administrator identities into Aster.

| Risk | Control and residual limit |
|---|---|
| Thinking and repeated tools saturate the one-slot inference service | Bounded requests/queue, time/token budget, measured speech and other-consumer impact, independent experiment stop; shared-host failure remains |
| Incomplete/stale evidence produces a plausible wrong diagnosis | Source/time/target/exit status and truncation metadata; follow-up observations; separate observed facts from hypotheses; held-out wrong-cause variants |
| Expanded tool loop bypasses policy or leaks secrets | Registered targets and typed arguments; credential-free fixtures; source-local sanitization; broker denial tests; no general shell/admin identity |
| Cloud escalation leaks personal material or creates unbounded cost | Local-only personal default, explicit provider/egress policy, sanitized packets and spend limits; cloud unavailable result without unsafe fallback |
| Repair succeeds partially or rollback harms unrelated work | Exact target/parameter/state binding, retained checkpoint, independent postchecks, uncertain-outcome reconciliation and narrow rollback |
| Evaluation leaks solutions or becomes endless tuning | Development/holdout separation, frozen manifests and independent review; finite trial/configuration cap; failure can select a narrower role |

Doctor/monitoring must cover actionable tool/model failures, queue pressure, stale observations and verified job outcomes without secret or prompt labels. Existing backup/recovery covers accepted configuration, adapter versions and durable incident state only after privacy/retention review; prove an isolated restore and keep human recovery independent. Update the human wiki, derived Aster snapshot, operational references and runbooks after accepted implementation, preserving provenance and honest role labels.

NetBox, physical diagrams, DNS, certificates, firewall and Homepage require no change for this documentation adoption. Assess them again for each concrete deployment; do not create infrastructure merely to satisfy a checklist. Authentication/authorization, service identity and credential custody belong to AI-PAM and the service-specific capability register. No new schedule is deployed now; future workers need concurrency, missed-run and last-success evidence. Security inventory must record versions, identities, revocation and removal of temporary access.

B60 inference engineering remains a linked, independently bounded supporting project under its own authorization. Personal email/calendar analysis remains a separately scoped module in this programme. Neither is a prerequisite to initial read-only sysadmin usefulness.

Evidence: [September 28 assessment](evidence/2026-09-28-sysadmin-readiness.md), [illustrative live diagnostic results](evidence/2026-09-28-sysadmin-diagnostics.json). These checks are neither a blind benchmark nor a thinking-enabled Qwen trial.
