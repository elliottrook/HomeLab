# Research log — 2026-09-25

## Harness follow-up

Jason asked to evaluate Hermes as a replaceable harness, compare current alternatives and recommend one implementation project document. Added `HARNESS-ALTERNATIVES.md`, linked it into the main assessment and drafted `Aster-Adaptive-Computing.md` outside the repository. Preserved the initial assessment/log/manifest under `revisions/initial-assessment/`.

Reviewed official Pydantic AI minimal loop, optional harness, slim installation, custom provider and durability documentation; LangGraph persistence; Pi core (old upstream URL redirects to earendil-works/pi); OpenAI Agents SDK; Agno; Microsoft Agent Framework; Google ADK; CrewAI Flows; smolagents; Deep Agents; OpenClaw; and Hermes. Web results are retained as `harness-research-1.json` through `harness-research-6.json`. The OpenAI documentation skill was used for its SDK portion.

Source reconciliation: a search result described an OpenAI SDK maintenance-status notice that was not present in the fetched page/official Markdown. That status claim was excluded. The web tool could not ingest the Markdown content type, so the official Markdown was fetched read-only through Python urllib and retained as `openai-agents-sdk-source.md`. No recommendation depends on the inconsistent search snippet.

Rechecked the exact historical Hermes/DeepSeek harness measurements in Local-AI. They demonstrate historical prompt/configuration overhead, not current universal relative framework performance. No candidate was installed, no new model run, and no speed/memory benchmark claimed. Recommendation is architectural fit: retain Aster baseline, evaluate minimal Pydantic AI first, selective LangGraph for explicit resumable workflows, Pi conditional on integration value.

The proposed single project is a monitored foundation release with M0–M7 gates; later programme releases remain explicitly bounded. It does not authorize deployment or automatic promotion. Report links and artifact hashes were rechecked after the supplement.

## Initial assessment log

Read-only architectural assessment. No repository or production modifications authorized or performed. Artifacts are outside repositories.

1. Read governance, portfolio, architecture, hardware, Aster operations, Second Brain, Local AI, AI-PAM, PA and bounded action records.
2. Found local main 586457f behind cached origin/main e50b670 by 15 commits. Working tree has pre-existing changes; preserved. Latest AI-PAM evidence differs materially from checkout. Cached github/main is stale and is not evidence of remote mirror failure.
3. Snapshotted non-secret tracked documentation and relevant source from cached origin/main; source-manifest.json retains per-file hashes. These are evidence copies, not repository migration.
4. Live read-only Proxmox inspection confirmed OpenBao LXC 117 running; Aster 104, inference 110, speech 116 running; VM 105 stopped; Xeon E5-2698 v4, 80338 MiB memory, 47248 MiB available at one instant, zero swap used; B60 bound to xe. PVE 9.2.20 differs from old M0 record.
5. Local aster-knowledge-mirror sibling is absent; wiki/reference siblings exist. Octelium/Jev/Decision Plane/Learning Plane terms not found in current tracked architecture search; absence does not prove undeployed.

6. Read-only direct SSH located the Forgejo repository under `/var/lib/forgejo/data/forgejo-repositories/jason/homelab.git`. An initial guessed historical `gitea-repositories` path failed; it was not treated as absence. `git rev-parse refs/heads/main` on the actual repository returned e50b670b906f397e1e70b6d51cf07e88235ac5c5. `git ls-remote https://github.com/elliottrook/homelab.git refs/heads/main` from the guest returned the same ref. No fetch or push was performed.
7. Inspected current AI-PAM, Companion, PA, Lab Operations and ARR evidence against historical plans. Current main records AI-PAM M0–M5 completion and connected Green Forgejo read integration, with native parity/write/final gates remaining. PA M0 is complete but implementation paused. ARR fixture graduation is not a natural production-remediation demonstration.
8. Read-only service queries confirmed Aster, broker, approval and Forgejo MCP gateway active on 104; llama service active and Ollama inactive on 110; speech on 116; OpenBao 2.6.3 on 117; Prometheus/Grafana on 109. The inspected Hermes gateway was inactive and no matching loaded units returned. This was not an exhaustive user-process audit.
9. Source hashes matched for live Aster agent, Lab Operations, broker core, broker approval service and Aster approval bridge. Broker transport hash differed. Reading that non-secret source showed the relevant code matched and the meaningful file difference was the opening descriptive docstring (“synthetic-only M2” versus the updated description). A copy is retained as `live-broker_service.py`; the copy has an additional terminal blank line introduced by artifact writing, so it is not asserted to preserve the live file hash byte-for-byte.
10. Ran the existing broker synthetic suite in the disposable source copy: 36 tests passed. Added two independent synthetic boundary probes using disposable databases: a different registered caller consumed another agent's request; an approved Yellow request remained consumable after demotion to probation. Results are in `broker-probe-results.json`. No production database, real approval or execution was used. These findings establish code-path gaps, not a demonstrated remote exploit or a complete security audit.
11. Inspected approval trust flow. The broker approval service trusts the allowed Aster process's supplied actor/assurance metadata; the Aster HTTP bridge validates identity. Explicit approver entitlement and independence from the model-facing process need review before expanding users/agents. Atomic consumption/concurrency needs testing; this assessment did not establish a race exploit.
12. Reviewed current infrastructure/hardware, network, backup/restore, identity, monitoring, source authority and project status evidence. Current running guest configured limits sum to about 73 GiB; instantaneous free/available host memory is not a safe additional allocation budget. Most runtime components share one Proxmox host. No machine purchase is recommended for the first experiment.
13. Reviewed related recommendation, news, document, media, subtitle, acquisition, storage, surveillance, Mac administration and external-agent pilot plans. Inventory distinguishes implementation records from proposed work, retired/declined plans and fresh observations. Peripheral reviews focused on purpose, status, architecture, dependencies, evidence and close-out; this is not a complete code audit of every project.
14. Primary-source research compared decision engines, routers, workflow engines, authorization engines, evaluation/observability platforms, serving, registries, retrieval, calibration and feedback optimizers. Tool results are retained in `research-web-1.json` through `research-web-8.json`. The assessment links supporting primary pages next to technology claims. External performance claims were not used as lab measurements.
15. Synthesized a federation under one programme. The first recommended test is read-only multi-capability routing with a strong rules baseline; a negative learned-router result is acceptable. The Learning Plane is both an independently governed subsystem and a slower cross-cutting control loop, not a runtime dependency or authority source.

## Source and verification ledger

| Evidence | Method / reference | Confidence and limitation |
|---|---|---|
| Repository baseline | Local Git status, branch/worktree/log inspection; direct remote ref queries | Exact main commit verified; local dirty work preserved |
| Project records | `source-snapshot/docs`, portfolio and manifest | Historical claims/intent; no automatic equivalence to runtime |
| Runtime guests/hardware | Direct SSH, `pct`/Proxmox read-only resources and service/version projections | Snapshot only, no sustained performance or availability claim |
| Broker code boundary | Reviewed source + live hashes/transport read + synthetic probes | Relevant path reproduced without production effects; broader exploitability not established |
| Learning/calibration/tool options | Official repositories/docs and research papers linked in assessment | Capabilities, not measured fit for this lab; live docs can change |
| Sibling knowledge repos | Local status/commit and bounded content review | Cached remote refs may be stale; no synchronization performed |

Key live hashes recorded during inspection:

```text
aster_agent.py          8777687ce97055d2db3254aa6b30ddf37fc61e73dac2bd18008cbea3fef1a8b6
lab_operations.py       0508fd95bfb71a41c55c7590538d1ed352a0d0d48211ffafe453230aa4def5f0
broker_core.py          c8f95571ab5b7be1783fe54394047a8d5c40d9cc9121ffcbdc7ad1af99a87cb1
broker approval service a73625fa3b68fe3a5e65f8960b6c96d9fec8fbf4c9dbdc75fe4136a5625c50d8
broker_approvals.py     3e376175640d7da84ab4e47b5bbc5e06075e0ce477283df2ae979e8ed44b1b0c
live broker_service.py  a45b2ff47fce65dd6c16a204979f00a9636fde4d82b799be14b867a91bf152af
repo broker_service.py  143b1d859b683b798a2a48b1b3e4c27cafd6ddcc31accd03e941b79223827890
```

Recent architectural provenance in Git:

```text
e50b670 2026-09-25 Require native Companion AI-PAM parity
c2aeb87 2026-09-25 Close OpenBao root recovery window
9c57a40 2026-09-24 Connect read-only Forgejo MCP gateway
2a0b2b9 2026-09-24 Open broker-only OpenBao service path
7297f0c 2026-09-24 Record Forgejo read credential gate
b091330 2026-09-24 Begin read-only Forgejo MCP pilot
798fe3d 2026-09-24 Verify Forgejo MCP release provenance
26fe7e1 2026-09-24 Complete AI-PAM probation lifecycle
74334af 2026-09-24 Complete AI-PAM management milestone
26854c3 2026-09-24 Deploy AI-PAM management candidate
b3619ce 2026-09-24 Complete AI-PAM mobile approval milestone
3af16b6 2026-09-24 Fix Companion approval inbox access
```

## Research limitations and unresolved questions

- No credentials, unseal shares, private keys, raw secret stores or production approval requests were inspected.
- No production fault injection, reboot, stop/start, external API mutation or new model installation was performed.
- Current host, service and hash observations are snapshots; end-to-end restoration and household failure behavior require future bounded drills.
- Personal workload prevalence, label quality, routing calibration, downstream outcome quality and sustained service objectives are not yet measured.
- Jev commercial/privacy/retention terms and comparative local-workload performance remain unverified; documentation alone does not authorize private exports.
- Octelium or other relevant work outside the searched tracked/local repositories may exist. It is explicitly UNKNOWN.
- The source manifest is a reproducibility aid, not proof that every copied file was read line by line. Core architecture/security and relevant project sections were reviewed; no exhaustive dependency/source-code audit is claimed.
- Report artifacts were written outside project repositories. No migration, archive, commit, push or production modification was performed.


## 2026-09-25 — M1 deployment preparation follow-up

Read-only service/hash/status projections on104 and read-only Authentik ORM/source projections on106 verified provider26 owner binding, subject mode, flow stages, generic ACR and the distinct authentication-method behavior. No tokens, sessions, provider secrets or recovery material were queried. The exact observations and current limitations are in [M1 deployment plan](evidence/M1-deployment-plan.md). Official OAuth2 and WebAuthn documentation was opened, but installed-source evidence governs the claim mapping. The generic ACR cannot safely be selected as passkey assurance.

Concurrent AI-PAM M6 deployment invalidated the first transport baseline; it was caught before any mutation. Re-queried hashes and service commands, matched M6's worktree source to deployed transport and preserved it while adding caller binding. Added fake-gateway denial tests; combined broker suite57 passes, staged Stage1 subset37 passes, legacy approval compatibility passes. This task has made no production or remote Git changes. A separately owned pending M6 request and deployment approval remain gates.


## Approved Stage1 execution — 2026-09-25

Jason approved the exact two-file LXC104 change. Source and database preflight,
protected backup/restore,45 guest tests and legacy approval compatibility passed.
The installer raced Type=simple socket readiness and failed closed. Read-only
diagnosis followed by one bounded same-candidate start passed. No DB restore,
credential/grant/gateway change or target write occurred. The full ten-minute observation passed; [deployment record](evidence/M1-stage1-deployment.md) holds the
exact scope, hashes, checkpoint and limits. Stage2 and Git push remain excluded.


## Offline M2 continuation

Built a synthetic-only candidate contract layer and extracted Aster selector
adapter without importing the application.28 tests and 12 fixture comparisons
pass; local timings and full source/evaluator provenance retained. No tools,
models, network or new dependencies. Existing Stage2 bridge/service suites pass
10+10; real assurance provenance remains an external verification gate.
Read a5e8b22 alternate lifecycle tests/admin diff during AI-PAM integration;
requested invariant coverage mapping instead of deleting tests to green the suite.
AI-PAM owns that reconciliation; no overlapping source edit here.


## Isolated reconciliation with authoritative f25df18

AI-PAM published its independently authorized integration while read-only
comparison was underway. Pinned the resulting baseline; seven local commits
already contained, three unique M2 commits. No authority source replay. Preserved
remote M3/M4 work and explicitly namespaced the selector-only contract profile;
29probe +52harness +76broker +163Aster tests pass. Current manifests and complete
commit map are in evidence/M2-reconciliation. Primary dirty checkout untouched;
no push or deployment by this task.


## Published integration and next M4 gate

User authorized push7133f3f; the push returned up-to-date after concurrent
publication, and read-only Forgejo/GitHub checks verified the exact matching head.
Reused existing localaf2cc4f review candidate rather than repeating experiments.
Resolved its stale header against deployed Stage1;56+29 tests and a network-blocked
164-event replay pass, with its original manifest unchanged. Prepared exact review
packet; no authenticated review or independent checkpoint custody is claimed.
The remaining gate needs human/external evidence, not another synthetic run.
