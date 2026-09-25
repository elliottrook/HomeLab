# Harness alternatives and implementation recommendation

Supplement to the [architectural assessment](ASSESSMENT.md), 25 September 2026. External capability descriptions are based on current official sources. Rankings below are **ARCHITECTURAL INFERENCE / PROPOSAL**, not lab benchmark results. No candidate was installed or executed during this comparison.

## Recommendation

Treat **Hermes as one replaceable harness**, not Aster's identity, authority or required operational brain. Retain the existing bounded Python Aster runtime as the production baseline. Evaluate **Pydantic AI's minimal typed loop first** for specialist reasoning and tool orchestration. Evaluate **LangGraph selectively** if explicit resumable branching and human pauses justify a workflow abstraction. Keep **Pi agent core** as a credible lean alternative, with the cost of a TypeScript integration boundary. No agent harness belongs in the deterministic household fast path.

This recommendation is deliberately conditional: adopt a library only if it improves maintenance, correctness or capability without unacceptable prompt/call/latency overhead. Aster remaining a small custom orchestrator is a valid winner. Do not build a new generic agent framework; reuse narrow libraries where they replace work you would otherwise maintain.

## What the Hermes evidence actually says

The [Local AI history](https://github.com/elliottrook/homelab/blob/e50b670b906f397e1e70b6d51cf07e88235ac5c5/docs/projects/completed%20projects/Local-AI.md) records an August 31 comparison: direct warm Ollama answered in 1.47 seconds; stock Hermes took 96.6 seconds with 19,422 prompt tokens, approximately 25 KB of system text and 57 KB of schemas for 19 tools. A stripped Hermes 0.20.3 profile reduced the main prompt to 2,177 tokens; a warm conversation took 12.2 seconds and a two-call terminal-tool interaction took 45.6 seconds. The same record separates an earlier GPU-driver/software-rendering failure from harness overhead. These are historical measurements of specified configurations, not a current cross-framework leaderboard or proof that all Hermes versions have identical overhead.

The record also tested a DeepSeek Harness developer preview: the stock configuration was heavy, while a tools-off profile was substantially smaller/faster. That reinforces the importance of configuration and workload. Do not promote that old preview as a current alternative without fresh provenance and documentation.

The dominant design risks are **unnecessary prompt material, too many exposed tool schemas and unnecessary model round trips**. Python versus TypeScript runtime microseconds may be immaterial next to local-model prefill. A tiny library can still create an expensive agent loop; a graph can be efficient if nodes execute deterministic functions and only necessary model calls.

## Separate four decisions

| Layer | Responsibility | Recommended starting point |
|---|---|---|
| Household execution | Supported deterministic intents, timers, device actions | HA/native local functions and explicit policy; no agent loop |
| Agent harness | Context preparation, model/tool loop, structured results, limits | Existing Aster baseline; minimal Pydantic AI challenger |
| Workflow durability | Persisted steps, waits, cancellation, recovery, reconciliation | Existing bounded queue initially; LangGraph for demonstrated graph needs; dedicated durable engine only when warranted |
| Authority and evidence | Identity, policy, grants, approval, evaluation and promotion | AI-PAM and separate evidence contracts, outside every harness |

Choosing Pydantic AI does not require Pydantic's complete coding harness, hosted observability, a new gateway or Temporal. Choosing LangGraph does not require a cloud control plane or autonomous supervisor. Durable execution and conversation memory are different: saving messages does not prove a tool effect can resume safely.

## Current alternatives

| Candidate | Documented capability | Fit and decision for this lab |
|---|---|---|
| **Existing Aster bounded runtime** | Repository implementation: deterministic tool preparation and bounded model interaction | **Baseline and safe default.** Lowest migration burden; retain source-specific safety contracts. Cost: custom state/retry/streaming code must be maintained. Extract small interfaces rather than rewrite it wholesale. |
| **Pydantic AI minimal loop** | Typed tools/results, dependency injection and provider abstraction; separate optional Graph/Evals packages. [Overview](https://pydantic.dev/docs/ai/overview/) | **First challenger.** Fits the existing Python code and schema-first architecture. Typed output reduces validation plumbing, not semantic errors or authorization needs. Measure actual prompts, repair retries and calls. |
| **Pydantic AI Harness add-ons** | Optional composable capabilities for planning, memory, workspaces and subagents, distinct from the minimal loop. [Harness documentation](https://pydantic.dev/docs/ai/harness/) | **Selective only.** Start without coding/research bundles, filesystem/shell, self-extension or memory. Adding the full suite could reproduce the overhead being removed. |
| **LangGraph** | Explicit graph state, checkpointers and separate stores supporting persistence and human-in-the-loop state. [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | **Second choice for complex workflows**, not required for every chat. Useful for calendar/web joins, pause/resume and explicit branches. Checkpoint storage requires retention controls; tool effects still require idempotency/reconciliation and renewed authorization. |
| **Pi agent core** | Stateful tool execution and streaming; current upstream separates the SQLite session backend from the core package. [Current upstream](https://github.com/earendil-works/pi/tree/main/packages/agent) | **Credible lean alternative.** Evaluate the embeddable core, not a full coding-agent shell. Current old `badlogic/pi-mono` URL redirects to this repository; pin actual package/version. TypeScript boundary increases integration/maintenance work for current Python Aster. Performance advantage remains unknown. |
| **OpenAI Agents SDK** | Application-owned deployment, tools, state and approval; SDK supplies agent loop and orchestration. [Official guide](https://developers.openai.com/api/docs/guides/agents/sdk) | **Viable comparator**, not first choice by default. Verify local endpoint semantics and tracing destinations before any private test. SDK use is different from adopting a managed cloud harness. No claim of benchmark superiority or mandatory OpenAI model use. |
| **Agno** | Agents plus explicit workflows containing functions, agents, branches and parallel steps. [Workflow docs](https://docs.agno.com/workflows/overview) | **Reserve candidate.** Could replace custom workflow plumbing, but adopting the surrounding platform would overlap existing UI, memory and observability. Test its SDK alone if the shortlist fails; published speed claims are not lab evidence. |
| **Microsoft Agent Framework** | Python/.NET agent and workflow framework, with migration paths from AutoGen/Semantic Kernel. [Official repository](https://github.com/microsoft/agent-framework) | **Reserve candidate.** Coherent option for that ecosystem, with no current lab-specific reason to prefer it. Its documented functional workflow API is experimental, so avoid making that interface the stable programme contract. [API status](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/functional). |
| **Google ADK** | Deterministic workflow-agent composition alongside model-driven agents. [Workflow agents](https://adk.dev/agents/workflow-agents/) | **Reserve candidate.** Relevant architecture, but local provider/serving compatibility must be demonstrated. No need to introduce another ecosystem unless it wins an identified workflow requirement. |
| **CrewAI Flows** | Stateful flow-oriented orchestration. [Flow docs](https://docs.crewai.com/v1.15.22/en/concepts/flows) | **Not first choice.** Explicit flows are worth distinguishing from model-driven crews. A manager/reviewer/team conversation on routine household requests adds no established value. Reject that pattern, not every possible use of the library. |
| **Hugging Face smolagents** | Agent library emphasizing model-generated code, with tool-calling options. [Official repository](https://github.com/huggingface/smolagents) | **Isolated research only initially.** Small codebase does not make generated-code execution a suitable infrastructure authority boundary. A constrained tool-calling configuration could be benchmarked later. |
| **LangChain Deep Agents** | Composable long-running harness with filesystem/context and delegation features; current documentation makes task planning opt-in. [Overview](https://docs.langchain.com/oss/python/deepagents/overview) | **Specialist research/coding worker, not household core.** Evaluate a minimal profile if needed; don't rely on older claims that every current version has the same defaults. Built-in tool limits do not constrain arbitrary custom tools automatically. |
| **OpenClaw** | Self-hosted gateway for channels, sessions, agents and device interfaces. [Official docs](https://docs.openclaw.ai/) | **Product-level alternative, not a small harness swap.** Worth consideration if replacing the assistant gateway/client stack is desired. Here it overlaps Companion, routing and administration, so no adoption merely to reduce Hermes prompt overhead. Policy claims require independent integration verification. |
| **Current Hermes** | Integrated skills, memory, tools and agent environment. [Official repository](https://github.com/NousResearch/hermes-agent) | **Optional comparator/specialist.** Preserve useful skills as versioned portable assets. No further assumption that Hermes must host orchestration or learning. A current minimal-profile retest is optional, not a prerequisite for progressing. |

No framework's guardrails, tool decorators, pause button or agent-to-agent protocol replaces AI-PAM's deterministic enforcement. No framework's memory or “learning” feature establishes the evidence lifecycle in the assessment.

## Why Pydantic AI is the first challenger, not a preselected winner

The fit is architectural: existing Python implementation, typed contracts and narrowly supplied dependencies. A slim installation is documented, allowing optional dependencies to be selected instead of adopting the whole package surface. [Installation](https://pydantic.dev/docs/ai/overview/install/). That supports a smaller experiment; it is not a measured latency claim.

Its custom OpenAI-compatible endpoint support is relevant to llama.cpp. However, provider/model profiles must match actual schema, reasoning and tool-call behavior; changing `base_url` alone does not establish compatibility. Test the exact local model and server, including malformed calls, streaming, cancellation and unsupported options. [Provider documentation](https://pydantic.dev/docs/ai/models/openai/).

Durability integrations are optional. For example, its Temporal integration needs a real workflow runtime; attaching an integration is not proof an ordinary HTTP request becomes durable. Defer that operational dependency until restart/recovery requirements justify it. [Durable execution](https://pydantic.dev/docs/ai/capabilities/durable_execution/temporal/).

## Harness contract

Introduce a small `run.v1` interface independent of library object models. Inputs: request ID, trusted principal reference, typed task/plan, authorized capability projection, scoped context handles, model/registry/policy versions, deadline, token/call/tool budgets, cancellation token and experiment ID. Outputs/events: started, model-called, tool-proposed, approval-required, paused, completed, cancelled, failed or uncertain, with typed result and usage references.

The harness may **propose** a tool intent. A separate adapter enforces current authorization and performs any real action. Experimental adapters only reach fixture tools. Tool discovery is filtered before prompts are built. Default tool set empty; schemas loaded only for the selected task. No global household memory or all-tools system prompt. Context cannot silently cross principal boundaries. Approval resumes must reauthorize and revalidate state, not merely replay a previously allowed call.

Budget policies include maximum model calls, tool attempts, tokens, wall time and fan-out. Expiry must stop dispatch, not just stop rendering the response. Cancellation distinguishes “not dispatched,” “in flight” and “outcome unknown.” Pin the harness, provider adapter, prompt, tool schema and model artifacts for each run. Trace contents remain minimized.

## Fair evaluation before migration

Keep the routing-engine experiment and harness experiment separate: a better classifier cannot establish that its surrounding harness is better. Reuse the same capability fixtures and outcome schema, but control the factors independently.

**Initial shortlist:** current Aster; Pydantic AI minimal; a small LangGraph implementation for the multi-step subset. Add Pi only if the measured shortlist leaves an unmet need or TypeScript is acceptable. Do not maintain ten prototypes. A current Hermes minimal profile may serve as reference, subject to an isolated pinned installation later.

Run two complementary comparisons:

1. **Controlled transport/loop test:** fixed model-response fixtures, identical tool responses and context. Measure harness CPU time, RSS, startup, serialization, schema inflation, cancellation and recovery. This isolates framework overhead without GPU calls.
2. **End-to-end task test:** pinned local serving model/settings, equivalent permitted tools and information, matched workloads and budgets. Measure success, total prompt/output tokens, model calls, tool retries, queue/prefill/decode time and p50/p95 task latency. Report warm/cold and controlled/shared-load results separately. Optimize each candidate within an equal documented tuning budget; identical scaffolding alone may unfairly handicap a framework.

Workloads: direct no-tool answer; one read tool; two independent reads; sequential dependent reads; ambiguous request; multi-label calendar/web fixture; malformed tool arguments; denied capability; approval pause/resume; restart around a simulated effect; dependency timeout and cancellation. Use the approximately 300-case routing corpus where applicable, with a smaller curated state-machine suite for workflow semantics. No production writes or real private exports.

Hard gates: no unauthorized fixture execution, no new egress, correct terminal/uncertain states, enforced budgets, principal isolation and compatibility with broker denials. Adoption additionally needs either a prespecified meaningful task improvement or a demonstrated maintenance/correctness benefit within an accepted overhead budget. Do not insist on faster wall time if the library buys necessary correctness cheaply; do not accept large latency regressions merely for fewer lines of code. Pre-register those tradeoffs before examining final results.

**Stop rule:** if the minimal custom Aster harness wins or no candidate demonstrates a material benefit after the bounded comparison, retain it. The programme proceeds with stable contracts and evidence collection. Harness replacement is a decision gate, not a project success requirement.

## One implementation project

Recommend **Aster Adaptive Computing — Foundation and First Evidence Loop**, now adopted at `docs/projects/AI Projects/Aster-Adaptive-Computing.md`. A complete review draft is [provided here](Aster-Adaptive-Computing.md). It is one governing project, with bounded work packages, not one enormous application and not a collection of new mini-project charters.

Its finite first release delivers: verified baseline and authority gates; stable contracts; a measured harness decision; open routing interface; minimal catalogue; privacy-preserving evidence; a shadow pilot; and one reproducible, reversible improvement or an evidence-backed rejection. Future household expansion, private/public live composition and operational autonomy remain explicitly gated later releases within the programme. This gives the project an achievable graduation point without pretending the entire long-term vision can be authorized at once.
