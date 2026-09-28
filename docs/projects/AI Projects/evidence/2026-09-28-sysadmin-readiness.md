# Aster sysadmin readiness assessment

28 September 2026 · Jason's HomeLab · read-only assessment and proposed changes

**Recommendation: keep Aster as the interface and local control layer, but change the unified project's immediate objective to operational diagnosis and verified repair. Give Qwen one finite, properly configured trial. Use a capable OpenAI reasoning model for sysadmin investigations if that trial fails. Keep private personal analysis local.**

The current Aster configuration is not a credible replacement for the sysadmin work demonstrated in your Codex sessions. Its limitations are partly deliberate product and architecture choices. The evidence does not justify saying the B60 and Qwen can *never* fulfill the role, nor promising that enabling thinking will make them equivalent to Codex.

## Evidence and scope

I inspected Git history, project and operational documents, Aster's source, evaluation code, the current adaptive-project branch, relevant Codex chat records, local SSH/tool configuration and selected live systems. I verified the authoritative Forgejo main ref directly. This is a broad capability assessment with detailed examination of Aster's critical path, not a line-by-line audit of every lab file or a fresh health check of every device.

The snapshots differ:

| Source | Observed revision/state |
|---|---|
| Forgejo main, directly queried | `ca22e788e78b6ec56b1a800da543f08bf30abcd2`; 792 reachable commits, 737 non-merge commits, 659 tracked files |
| Local homelab main | `d2f771d`; 750 reachable commits; includes September 27 repairs absent from the inspected published tree |
| Adaptive-project working branch | `8fd5f8d`, `codex/aster-m2-reconcile-20260925`; includes the later harness decision and S1 preparation |
| Unique commits across these three histories | 850; exported in the companion Git ledger |
| Remote main vs local main | 53 remote-only and 11 local-only commits |
| Remote main vs adaptive branch | 44 remote-only and 47 branch-only commits |

These counts include documentation, merges, experiments and work by multiple people/agents. Most commits use Jason's author identity; Git authorship cannot establish which AI performed every action. Relevant Codex chats corroborate representative work, including “Diagnose Aster and lab drift,” “Diagnose Video Archiver Failures,” “Aster Adaptive Computing — Stream A,” and “Assess AI Infrastructure Unification.” No count here is a claim of 850 successful Codex repairs.

## The job Codex has actually been doing

| Domain | Recorded work and practical competence demonstrated |
|---|---|
| Networking | VLAN/subnet design and migrations; UniFi management; AP switch recovery after reset; DHCP/SSID drift checks; Synology asymmetric routing; DNS, firewall and reverse-proxy diagnosis |
| Hypervisor and hardware | Proxmox guest provisioning and memory adjustment; guest recovery; Intel B60 driver/backend/BAR investigation; inference startup and GPU-binding recovery |
| Backups and resilience | Multi-platform configuration exports; guest backup coverage; TrueNAS hub and encrypted off-site relay; restore proofs; backup schedule/ACL repairs; UPS/NUT monitoring and shutdown coordination |
| Identity and access | Authentik, OIDC/passkeys, NPM and owner-only policies; browser/native-client acceptance; approval-service repair; credential broker and OpenBao integration |
| Observability | Doctor scripts, Prometheus/Grafana/Beszel, alerts, certificate/backup freshness, drift review and parser repairs |
| Applications and data | ARR/Jellyfin migration and integrity tools; media metadata and duplicate repair; archive encoding; Paperless deployment/IP correction; NetBox inventory and startup recovery; Frigate camera/recording diagnosis |
| Engineering and operations | Read source/config/logs, test competing causes, write patches and regression tests, preserve checkpoints, deploy authorized changes, verify real outcomes and document recovery |

Three particularly useful comparisons:

1. **ARR second login — `c4afd8b`.** Codex compared responses with and without forwarded client-address headers, related that to ARR's local-address authentication exception, and changed only the protected proxy routes. It checked that unauthenticated and forged-header requests still hit Authentik. This required reasoning across browser, NPM, Authentik and application settings.
2. **Doctor/Aster failure — `a05047a` and subsequent repairs.** The visible iPhone failure led to a downstream shell/parser crash: current archiver events no longer matched the legacy parser, and an empty Bash array aborted reporting. Separately, approval configuration and passkey assurance required repair. Treating the symptom as merely an iPhone connectivity problem would miss the causes.
3. **Video archiver — `d2f771d`, published as `ca22e78`.** Codex identified missing stream bitrate with usable Matroska BPS metadata and a separate Jellyfin authentication-header change. The recorded repair includes tests, checkpoints, two bounded production retries, independent media validation and completed scan verification. The two replacements saved about 2.49 GB before snapshot retention.

These are the appropriate benchmarks. Answering “which guest runs inference?” is useful, but tests a different level of capability.

## Access and tools: an unequal comparison today

**Live verified:** root SSH sessions to Proxmox, TrueNAS and OPNsense; Forgejo access sufficient to inspect repository refs. Through Proxmox, `pct exec` read the running Aster/inference guests. This is substantial administrative reach. Existing SSH configuration also names Docker, Arista, Frigate, NUT, Synology and speech targets; those individual logins were not all revalidated in this assessment.

Local tools include SSH, Git, Python, curl, GitHub CLI and Codex CLI. This chat also exposes shell/file editing, web research, GitHub connector tools, browser/native UI tools, and Codex chat/project inspection. Installed CLI presence is not proof of each service's current authentication. Email/calendar integrations are not thereby available.

I can read the lab repositories, operational references and configuration and use already configured identities subject to platform controls. This session's filesystem write scope differs from the homelab project's saved configuration; technical access is not blanket permission to change production. Repository rules also distinguish local commits from remote publication. No secret values or private key contents were included in this assessment.

**Aster has a much narrower view.** Its standard functions read curated knowledge, time, health and sanitized reports. The documented Forgejo report omits source, diffs, commit messages and action logs. Its NetBox report is bounded inventory. Normal advisory tools do not provide arbitrary shell, filesystem editing or arbitrary network targets. There are separate bounded Doctor/backup jobs, ARR action mechanisms and AI-PAM interfaces, but these do not constitute a general diagnostic workstation.

Aster therefore cannot reproduce much of Codex's work even with a stronger model dropped into the same endpoint. It needs additional diagnostic capabilities and a workflow that can use their results iteratively—not the wholesale transfer of administrator credentials into a model.

## Why current Aster underperforms

**1. Thinking is explicitly disabled.** The live service command contains `--reasoning off --reasoning-budget 0`. It serves Qwen3.8-27B UD-IQ4_XS with llama.cpp build 11081, commit `161755f29`, Vulkan, one 8,192-token slot. The Qwen model card supports thinking and tool use, but that does not prove the installed quantization/runtime's task quality. [Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B).

**2. The main chat path is a one-pass answer generator.** `build_payload()` chooses tools from keyword rules, preloads their results and removes `tools`/`tool_choice`. The system prompt tells the model not to request another search. A residual non-streaming tool-call loop exists in the code, but the normal payload and progress-streaming path do not provide a general iterative investigation. Raising `ASTER_MAX_TOOL_ROUNDS` alone does not fix this.

**3. The answer budget is tight and inconsistent.** Source defaults are 160 ordinary / 112 health tokens. The inspected live environment overrides ordinary answers to **500**, with a 180-second upstream timeout and four configured tool rounds. The prompt still asks for roughly 100-token answers. The health-specific default remains separate. This is a poor fit for a diagnosis, evidence, proposed repair, risk, rollback and verification response.

**4. Evidence is limited and sometimes stale.** Keyword retrieval, curated snapshots and summary reports can answer known questions, but often cannot supply the logs or config details that distinguish competing incident causes. Many retrieval boosts explicitly favor known topics. A new task requires the ability to find missing evidence, not only better ranking of existing excerpts.

**5. Graduation overstates the operational role if read loosely.** Historical results include 28/28 sysadmin answers, 20/20 HA answers and 60/60 mirror answers. The inspected sysadmin suite largely evaluates required/forbidden strings for facts, provenance, recovery order and refusals. These are useful regressions, but do not demonstrate novel incident resolution. Repeated retrieval and wording corrections are not model weight training or proof of generalization.

**6. Latency makes larger reasoning budgets consequential.** The September 25 B60 engineering record gives a documented control of about 193.3 prompt tokens/s and 11.85 generated tokens/s, with some production responses around 7 tokens/s. These are historical measurements, not today's benchmark. At 7–12 tokens/s, 2,000 generated reasoning tokens alone would take roughly 3–5 minutes, before answer generation and other delays. A real trial must measure quality and total time together.

**7. Release state is fragmented.** The live Aster source hash is `f7b5c82b8a401162e5151a2c8289b061e3d4a8bb162fa9598997ed67081e99a1`; local main and published source differ. Comparing the retrieved live source with local main identified ten additional AI-PAM retrieval lines. The checked-in inference unit also names an older binary than the running service. These are reasons for reconciliation and a runtime manifest, not for resetting live systems to a branch.

## Direct diagnostic checks on the current runtime

Two read-only exercise prompts were submitted to the authenticated Aster sysadmin endpoint, with jobs and changes explicitly excluded. They are small illustrative checks, not a controlled model comparison or blind evaluation; historical solutions may be available in the knowledge corpus.

**ARR second-login exercise:** 89.69 seconds; 2,655 prompt tokens; 500 completion tokens; `finish_reason=length`. Aster treated Homepage as an authentication proxy and proposed native ARR IdP/callback/SSO settings. It missed the documented NPM/forwarded-client-address/local-authentication interaction, and the response cut off before completing verification. It did not claim to have executed checks. This is direct evidence of an architecture-grounding and usability failure, not merely dissatisfaction with its writing style.

**Video-archiver/Jellyfin exercise:** 65.21 seconds; 2,626 prompt tokens; 340 completion tokens; normal completion. Aster correctly separated the two symptoms and recognized bitrate fallback and header compatibility as likely causes. However, it asserted that Jellyfin 10.11.11 was in use, while the September 28 verified runbook records 12.1.0. It recommended an ambiguous header form and omitted checkpoint/original-preservation requirements, media decode/duration verification and actual library-scan completion. The prompt supplied much of the diagnostic evidence, so this demonstrates partial interpretation, not independent discovery. The stale version assertion also exposes a knowledge-freshness problem.

Both raw answers, timings and token counts are saved in `aster-live-diagnostic-checks.json`. No production jobs or changes were requested. Conclusions about model replacement do not rest on either anecdotal case alone.

## Will the unified project deliver the required sysadmin?

**Not on its current acceptance criteria.** It builds worthwhile authority, contracts, evidence storage, routing comparisons and controlled promotion. Those foundations should remain. But the programme can succeed at selecting capabilities and recording a change decision without ever demonstrating an unfamiliar incident diagnosed and repaired.

The newer branch's M3 decision retains bounded Aster after controlled fixture comparisons. PydanticAI's measured millisecond overhead and extra approximately 22 MiB do not answer whether a real investigative workflow is better. The accepted S0 routing experiment used ten exposed development families: keyword completeness was 4/10 request-only and 3/10 with context; fixed-nearest was 6/10 and 8/10. These are descriptive routing results, not Qwen sysadmin results. A disposable VM took roughly 135 seconds to run 0.118 seconds of evaluator work. The evidence process is valuable, but its current focus is consuming effort without proving the capability you most need.

Update the project with the concrete SA0–SA5 workstream in the companion amendment. Prioritize one complete diagnostic path, representative incidents and verified repair. Keep routing/learning infrastructure proportionate and out of the critical path to useful read-only investigations.

## Qwen-only versus hybrid

**Preferred first step: Qwen-first, not an immediate hardware purchase.** Trial the current local model with a genuine tool loop, suitable reasoning/output budgets and live diagnostic evidence. The B60 has 24 GB VRAM; that constrains model/context choices but does not by itself determine intelligence. Larger context, another GPU or a faster backend cannot compensate for missing tools or a one-pass prompt. [Intel B60 specifications](https://www.intel.com/content/www/us/en/products/sku/243916/intel-arc-pro-b60-graphics/specifications.html).

**Practical fallback: one Aster interface, local personal analysis, OpenAI sysadmin reasoning.** Let a deterministic local orchestrator select the provider. Qwen handles private email/calendar analysis, summaries and suitable bounded tasks. A capable OpenAI reasoning model handles difficult sysadmin investigations through sanitized observations and locally executed tools. Keep policies, credentials, execution and verification local. The cloud model must pass the same incident tests; the API alone does not recreate this Codex environment.

Use a proper Responses API adapter for an OpenAI reasoning model; for example, GPT-6 Astra tool calling is supported through Responses rather than Aster's existing Chat Completions route. Explicitly configure reasoning and validate availability/billing at implementation. [OpenAI reasoning documentation](https://developers.openai.com/api/docs/guides/reasoning), [tool integration documentation](https://developers.openai.com/api/docs/guides/tools).

Do not make weak Qwen self-confidence the sole escalation decision. If it fails the sysadmin gate, select the stronger provider directly for that role. If it passes routine triage only, graduate that narrower scope. Keep personal content local unless separately authorized, and preserve independent human/local recovery when cloud or Aster is unavailable.

Email/calendar analysis is also unfinished work: the archived personal-assistant plan records iCloud discovery and a pause, not a deployed integration. Reintroduce it as a scoped local module. Schedules should be deterministic workers; Qwen can explain their results rather than inventing privileged commands nightly.

## Recommended decision now

Accept that Aster currently qualifies as a constrained advisor and bounded job front end, not your general sysadmin. Amend the existing programme, reconcile the release state, and run the finite Qwen investigative trial before expanding research infrastructure or buying hardware. If the local trial cannot meet quality and latency targets, adopt the hybrid architecture. This preserves your Qwen preference while putting a clear limit on further effort that does not produce useful administration.

**Assessment limits:** no production configuration was changed; no benchmark with thinking enabled, alternative model, larger context or cloud provider was run; no claim of eventual Qwen parity or impossibility is justified. The inspection and two diagnostic calls cannot establish overall availability, workload headroom or a statistical incident success rate.

**Local evidence index:** `services/aster-agent/aster_agent.py`; its systemd units and `evals/sysadmin-graduation.json` / `run_evals.py`; `docs/reference/Aster-Operations.md`; `docs/projects/B60-Inference-Engineering.md`; `docs/projects/AI Projects/Aster-Adaptive-Computing.md`; branch `8fd5f8d`'s `evidence/M3-harness-decision.md` and S0 `run-v5b-corpus/README.md`; `docs/runbooks/ARR-SSO-Repair-2026-09-27.md`, `Lab-Health-Review-2026-09-27.md`, `Video-Archiver-Repair-2026-09-28.md`; `services/aster-lab-operations/README.md`; archived `Aster-Personal-Assistant.md`. Paths are relative to the inspected homelab repository or explicitly named branch. The Git ledger retains full commit identifiers for further inspection.
