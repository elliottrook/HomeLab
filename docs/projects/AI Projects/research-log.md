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


## M3 representative-label design

Inventoried four payload cases, eight tool-loop scenarios, 30 authored routing
families and 12 selector fixtures; none became human gold. Drafted bounded S0-only
pilot/held-out protocol and empty forms. Review found missing semantic privacy
inheritance and ambiguous execution/label provenance; corrected those, specified
all-test second-human review, fixed statistic definitions and explicit content
review. 17 new tests pass; 73 total harness/evidence tests. Empty validation output
contains zero cases and no authority. Primary calibration references checked;
no model/cloud execution, real collection, install, deployment or push occurred.
M4 acceptance/custody and M3 human protocol/readiness decisions remain open.


## 2026-09-25 — protocol approval and custody readiness

Recorded the narrowly conveyed human design approval against the original protocol
commit/hash. Prepared a documentation-only readiness comparison: paper pilot versus
separate human OS account versus restricted Forgejo storage. Paper minimizes runtime
complexity but cannot supply machine evaluation without a later import decision.
No custody location/account, labels, cases, collection workflow or authentication
evidence was invented. Numeric retention and future acceptance tests are proposals,
not executed controls. Review clarified incident preservation must receive an explicit
human custody/deadline decision rather than unconditional destruction within 24 hours.
M4 approval remains distinct. Publication requested by Jason; remote reconciliation
must preserve the newer AI-PAM M7 work.

Technical review rejected the initial paper-default recommendation as inconsistent
with approved durable S0 Git retention and unnecessarily obstructive to evaluation.
Revised to recommend repository-native, human-reviewed S0 train/dev forms/validator;
no collection from implementation approval. Private/secret facts remain excluded.
Separate custody applies to later hidden tests and the distinct M4 checkpoint gate.


## Implementation-only S0 tooling

Recorded scoped implementation approval from coordinating task, on published
4702ee0. Added empty local forms and stdlib fixture-only reference/state checker.
Synthetic in-memory fixtures exercise transitions and adversarial privacy/revision
failures; no pilot content or human receipt was created. 23 new / 96 total tests
pass. No network/write/staging path; all authority outputs remain false. Review
requested before commit. Operational collection/retention and M4 gates remain open.

Technical reviewer independently reran the initial 18 added / 91 total tests and
accepted the non-collecting candidate. Subsequent local additions passed 23/96.
Review permits local commit only; next gate remains collection/retention approval.


## 2026-09-25 — direct bounded pilot approval

Recorded direct approval of September 26–October 25 manual pilot, including exact
case-by-case review and durable-retention limits. A coordinating message suggested
September 25; the direct approved statement governs. Clock confirms collection
not yet open. Read-only checks: `/private/tmp` Time Machine Included; existing
per-user temporary root Excluded; Spotlight disabled. No backup configuration
changed and no cases/data directories created. Third-party capture remains unknown.
No scheduler, model call, evaluation, deployment or push.


## 2026-09-26 — batch 1 direct human acceptance

Direct “Approve” response accepted all ten displayed cases and proposed labels.
Preserved exact proposal bytes and separate per-case/hash-bound acceptance record.
This is personalized review, not human authorship or independent gold. No timing
inferred; effort gate remains unknown and next batch is paused. No router/model
evaluation or execution; fixture-only validator remains unchanged.


## 2026-09-26 — batch 1 reported effort

Jason reported five active-review minutes across ten cases. Recorded as approximate
aggregate self-report; derived average30 seconds, no measured median/per-case times.
Conditional median bound50 seconds clears effort stop rule; zero unresolved
annotations. Batch2 remains AI-proposed and requires human content/label decisions.


## 2026-09-26 — batch 2 acceptance

Direct “accept” response accepted cases11–20 and their proposed labels without
revision. Preserved exact proposal/hash and separate manual acceptance receipt.
Five train/five dev; total20 accepted families. No independent-gold or timing
claim; batch2 effort remains unknown. No evaluation, execution or push.


## 2026-09-26 — batch 2 effort and final-batch preparation

“Same” resolves to five active-review minutes for batch2. Preserved aggregate
self-report and conditional median bound, no invented per-case timings. Verified
batch3 scratch directory Time Machine Excluded and Spotlight disabled before
writing. Final ten proposals remain outside Git pending case/label approval.


## 2026-09-26 — final pilot acceptance and bounded close-out

“approve 3 minutes” accepted final10 cases/labels and reported aggregate effort.
Verified all30 per-case hashes and nine artifact hashes; 20train/10dev, 3/stratum.
Total reported review13minutes. Recorded anchoring/nonblind proposal-review limits,
no independent annotation-cost or routing-quality claim. Collection closed at cap.
No evaluation, deployment, further case creation or push.


## 2026-09-26 — offline comparison planning

Read existing stdlib rules/Nearest implementation; its default evaluate entry point
tunes on another corpus and is unsuitable here. Pinned it without invocation.
Proposed fixed0.2 similarity threshold, no tuning, three engines/two input profiles,
all10dev cases retained in denominators. Context hints and exposed labels preclude
generalization claims. Privacy/model selection remain unmeasured, not backfilled
from reference labels. Wrote plan and null implementation pins; no runner executed.


## 2026-09-26 — implementation-only descriptive evaluator

Direct approval covered local code/tests, not pilot execution. Added bounded manual
evidence adapter and descriptive metrics plus pinned-source fixture comparison.
26 focused /122 full tests pass using invented in-memory records only. No accepted
case routed or fitted. Documented cooperative-budget and missing OS-launch/output
controls; no readiness claim from sandbox-exec existence. Technical review requested.

Review accepted the26/122-test candidate. Added family-alignment checks and three
more adversarial cases;29/125 pass. Harmless sandbox-exec true probe failed with
Operation not permitted (exit71); no corpus run or workaround. Recorded environment
blocker and future frozen-root/exclusive-output/hard-timeout requirements.


## Launcher readiness design and harmless primitive probes

PATH has sandbox-exec/Python, not queried container/namespace executables. Existing
Mac/Python support parent process control; six disposable fixture probes pass after
observing/scrubbing an OS-injected environment key. Full suite131 passes. Retained
blocked nested sandbox result; no weaker substitute. Documented hard isolation,
external-root, memory containment and recovery gaps. No accepted corpus accessed.


## Existing context inventory — read-only, pending review

Inspected established PVE inventory and bounded version/tool/image metadata in
LXC100/104 via direct read-only SSH. Shared Docker100 has Python3.13.5/systemd257/
Docker29.8.1/cgroupv2; no standalone minimal Python image observed.104 carries
authority services;105 is stopped recovery guest. No verified dedicated test
context. Official tagged systemd257 manuals used after rendered docs403.
Proposed conditional100 fixture feasibility design only, no worker/unit/container
created, accepted data accessed, install, infrastructure change or push.


## LXC100 feasibility candidate correction and local supervisor

Review caught invalid nested quoting. Replaced with fixed shlex-generated argv;
syntax/roundtrip/disposable local path tests pass. Added fixed-fixture-only Mac
supervisor: combined8KiB stdout/stderr bound, deadline, kill/reap, fallback command
representation and permanent remote denial.9 focused/140 full tests pass.
No remote command executed by supervisor, no accepted corpus access, no unit
started or live gate enabled. Candidate returned for review before commit.

Environment review found clear() only proved self-erasure. Added fixed locale,
systemd pre-start unset list, initial-key allowlist and early rejection before
probe imports/operations. Local invented environment tests never print values.
Added exact cleanup-mode checks and rejection tests; current13/144 pass.
Regenerated hashes; no remote unit or full payload executed, no commit yet.


## Full fixture-only probe state machine

Committed reviewed supervisor at1e506bd. Added exact fake-transport preflight,
health/DNS/control checks, ordered execution and cleanup/final verification.
Every transition has failure-injection coverage;17 new/161 full tests pass.
Uncertain ownership never authorizes stop/delete. No remote branch, accepted
data, actual DNS packet, unit lifecycle, install or push. Returned for review.


### 2026-09-26 — bounded LXC100 collector candidate

Local evidence: 15 new/176 full tests pass. Added byte/time limits to proposed
metadata collectors and PID/invocation checks to candidate ownership receipts.
No remote execution. Unloaded-unit recovery and lifecycle integration remain
UNKNOWN/unimplemented; see LXC100-CANDIDATE-EVIDENCE.md and pinned manifest.


### 2026-09-26 — integrated fixture lifecycle and recovery

184 full tests pass. Added durable intent/ownership records and receipt-guarded
cleanup; already-unloaded unit accepted only after verified completed execution
and matching canary identity with absent cgroup. Interrupted runs never replay
mutations. Live confinement and remote termination remain UNKNOWN. Candidate and
remaining-risk statement submitted for final technical review, no live invocation.


### 2026-09-26 — timing margin and manifest-bound one-shot candidate

192 full tests pass, including 8 focused timing/adapter tests. Fake-clock delayed
observations validate a single eight-second inspection deadline against the
worker's ten-second window. Fixed direct SSH and DNS adapters are implemented and
mock-tested; public invocation is disabled. Actual LXC100 support remains UNKNOWN.
Prior integrated checkpoint: `28a9e49`; current pins in the live-candidate manifest.


### 2026-09-26 — descriptor reads and conditional approval provenance

200 full tests pass, including 8 authority/read tests using temporary records and
stub execution. Bounded same-descriptor reads reject symlinks, unsafe files and
observed changes. External approval record binds the final manifest without a
hash cycle and records conveyed conditional authorization. All technical/operator/
execution release fields remain pending; no network/LXC invocation occurred.


### 2026-09-26 — coordinated single-probe release

Last preflight review passed in the coordinating task; it confirmed the exclusive
operator window and instructed release under Jason's conditional authorization.
Pending-gate checkpoint `eb1deef` preserves the preceding state. Release record
bound to regenerated final manifest; 200 full tests pass with real-record execution
mocked. No invocation by this preparation task. Final commit/hashes handed to the
coordinating task for its final verification and one authorized attempt.


### 2026-09-26 — run 001 safe read-only preflight failure

Copied/hash-verified the untouched five-record journal. No mutation intent or
ownership receipt. Coordinating task diagnosis reports an added container and
unbounded guest-root memory.max despite host-side 4 GiB LXC maxmem. Collector
assumptions need revision; this is not evidence of isolation failure. New attempt
requires separate journal, approval and fresh absent-state preflight.


### 2026-09-26 — unapproved attempt2 candidate

206 local tests pass. Dynamic inventory retains inactive containers in an exact
state baseline; fixed host-side pct accounting replaces invalid guest-root limit
assumptions. Guest MemAvailable/PSI and unit64MiB/no-swap/process limits remain.
New journal/approval identity and prior-run read-only proof prevent automatic retry.
No live diagnosis/execution by this preparation task; fresh approval still required.


### 2026-09-26 — fresh run002 approval conveyed

Coordinating task reports Jason's explicit `approve` for exactly one corrected
run002 probe once technically reviewed. Recorded separate provenance without
releasing the pending machine gate or inventing a final reviewed hash. No code,
manifest or run journal changed; no live action occurred.


### 2026-09-26 — captured pct output regression corrected

Added the full coordinator-provided host status fixture, including vmid/name/type/
tags and six pressure fields. Strict identity/metadata validation retains unknown-
field rejection. 8 focused attempt2 and 208 full tests pass. Corrected manifest
pins verified; machine gate remains closed. No live query or invocation performed.


### 2026-09-26 — reviewed run002 release-only preparation

Independent technical review passed. Updated stale approval language, exact fresh
approval provenance and released-record tests, with prepared execution mocked.
Eight focused and208 full tests pass. Final binding occurs after all pinned edits;
no invocation, fixed-journal creation, network query, commit or push in this step.


### 2026-09-26 — run002 failed safely in preflight

The coordinating task independently verified the released hashes and performed
the single approved invocation. Unit-state, path, guest-health and host-LXC-status
operations completed and resource telemetry was retained. The terminal record is
preflight failure with no mutation and no manual recovery requirement. No create,
worker, cleanup, remote-stop or corpus event exists. A later bounded DNS diagnostic
succeeded, so the exact failure remains UNKNOWN / REQUIRES VERIFICATION. Preserved
the seven-record chain, exact reviewed manifest/approval bytes and the one changed
pinned plan artifact under `run-002/`. The approval is consumed; no retry or push.


### 2026-09-26 — bounded failure-code telemetry

Implemented local-only failure boundary and class fields after run002 showed that
a broad `preflight` stage was insufficient. Codes are lifecycle-owned; classes are
limited to timeout, permission, I/O, validation and internal. Tests inject sentinel
exception text into DNS and journal failures and prove it is not retained. Default
denied transport remains distinguishable. Full suite: 210 passing. No live query,
retry, new approval, package, corpus or infrastructure change. Next decision is
whether a third fixture run has enough expected information gain to justify risk.


### 2026-09-26 — run003 go/no-go review

Decision: prepare a distinct candidate locally, but do not execute it. A final
one-shot can add evidence because both earlier attempts stopped before mutation and
the new bounded codes distinguish the unresolved preflight interval. Reusing the
run002 artifact is rejected. A disposable clone remains preferable for later
corpus/destructive work, but no verified ready target or safe spare-allocation
budget is established. Run003 must pin both evidence sets and obtain fresh approval.
A third pre-mutation failure ends live retries pending redesign.


### 2026-09-26 — run003 candidate prepared and reviewed

Created distinct attempt3 journal/manifest/approval identities. The launcher now
verifies both prior no-mutation evidence sets, including exact run002 reviewed and
consumed approval records, before any prepared invocation. Bounded failure telemetry
is the only execution-path change; commands and resource limits are unchanged.
Twenty-one focused and 213 full tests pass. Final manifest is
`188fc6a6e6ed8dda082e71c46e232145a782ad21c1ad03f795135a933ffc0c29`.
Technical review passed; human approval and execution release remain pending. No
SSH, DNS, live journal, package, corpus, infrastructure mutation or new push.


### 2026-09-26 — run003 namespace failure and verified recovery

The one approved run003 passed preflight, created the receipt-bound canary and
failed at payload readiness. Bounded evidence records `run-readiness` / `validation`;
systemd reports `226/NAMESPACE`, MainPID0 and no cgroup/runtime probe. Manual
recovery revalidated the exact invocation and canary inode/content, reset only the
failed transient unit and removed only that canary. Final unit state is not-found,
probe paths are absent, systemd is running and Docker state matches baseline.

This is a negative feasibility result for the reviewed namespace combination in
LXC100. No accepted corpus ran. The one-shot approval is consumed and run004 is
prohibited on this shared host. Next architecture work must examine a VM or a
different isolation boundary without weakening deterministic controls.


### 2026-09-26 — LXC100 retired as S0 execution boundary

Recorded an explicit architecture decision from the run003 negative evidence.
Do not bisect namespace directives on the shared household guest or weaken the
reviewed controls to force readiness. Accepted-corpus execution remains blocked.
A dedicated disposable Linux VM is the preferred future target, but VM105 remains
reserved/rejected and no capacity or placement is assumed. VM design needs its own
read-only capacity/network/image assessment and explicit creation approval.


### 2026-09-26 — disposable VM read-only feasibility

Proxmox reports 84.24 GB total /49.42 GB available memory at one instant; 17
running guests total78.38 GB configured maxima and28.70 GB observed use. Local-lvm
has665,394,887 KiB available. Existing Debian13.6 netinst ISO SHA-256
`65273beed27b2df543b68b65630ba525cfbad8df2b12035732b2dff87d6664e7`
matches Debian's archived checksum. Proposed design is1 vCPU,1 GiB RAM,8 GiB disk,
no vNIC/GPU/credentials, offline pinned input and bounded output. This is feasibility
evidence only: no VMID reservation, image download, VM creation or corpus access.


### 2026-09-26 — disposable VM concrete build gate

Selected a dated Debian13 generic qcow2 rather than netinst or the mutable `latest`
alias; observed published SHA-512
`a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c`.
Cloud-init NoCloud supplies an offline immutable seed. QEMU Guest Agent, vNIC,
credentials and shared filesystems remain absent. A strict 4-MiB/five-minute framed
serial capture carries a 2-MiB digest-bound result; rejection never auto-retries.
Planned gates are local parser/seed proof, stopped-state creation, bootstrap canary,
invented S0 fixture, then explicit boundary GO/NO-GO. No download, VM mutation,
accepted-corpus access or package installation occurred.


### 2026-09-26 — V0 bootstrap and serial candidate

Implemented a pure strict serial frame encoder/parser and deterministic offline
bootstrap-canary source renderer. Twenty focused and 234 full adaptive tests pass,
covering framing, bounds,
identity/digest checks, malformed/noncanonical JSON, candidate determinism, no
corpus/authority, no login/package/network config, systemd outer limits and
rejection of any guest interface beyond loopback. Ruby
parsed the generated cloud-config; persisted file hashes match the candidate
manifest. Candidate manifest SHA-256 is
`0d015cc70e6df5b31048fd203916dcaf0b783e8ecd3bbaae6b6c76f339610c47`.
No ISO, image download, VMID reservation, Proxmox mutation or corpus execution.


### 2026-09-26 — disposable VM V1/V2 negative result

Forgejo and GitHub mirror advanced to `dcc3623`. The dated Debian image matched its
published SHA-512 and stopped VM118 matched the reviewed one-core/1-GiB/8-GiB
networkless configuration. One approved bootstrap boot reported only loopback.
Cloud-init invoked `aster-s0-canary.service`, which failed before emitting a framed
result; the shutdown fallback powered off cleanly. Capture is 105,115 bytes, SHA-256
`23e071c370e952d64c08b678900121ee03098ec7444b1d26f5e5661fc9027fdb`, with zero
protocol records; strict parse result is `incomplete protocol`. VM118 remains
stopped, host/existing guests are healthy and unchanged, and no corpus ran. Exact
unit cause is UNKNOWN pending separately approved read-only offline forensics. No
retry or V3 is authorized.


### 2026-09-26 — V2 forensic cause and v1 correction candidate

An approved offline inspection attached VM118's stopped OS disk through a read-only
loop and mounted ext4 `ro,noload` (`norecovery`). The filesystem was clean, the
reviewed unit/canary/manifest hashes matched, and no result file existed. Seven
bounded journal records prove systemd failed before Python with
`status=209/STDOUT`: direct `/dev/ttyS0` output conflicted with
`PrivateDevices=yes`. Mount and loop cleanup were verified and VM118 remains
stopped. The v1 candidate retains private devices, writes the framed output to a
bounded file and delegates serial publication to the outer cloud-init lifecycle.
Twenty-one focused and 235 full adaptive tests pass. No new ISO or VM exists, no
boot or corpus run occurred, and V2b/V3 remain unauthorized.


### 2026-09-26 — V1b/V2b read-only preflight and frozen release

Proxmox preflight observed 48,981,213,184 bytes available memory, 664,145,554 KiB
available on active `local-lvm`, 68,233,444 KiB on active `local`, VMID119 free,
VM118 stopped and all service containers at baseline. The dated image SHA-512 and
checksum-file digest revalidated; v1 seed/ISO/release/run paths are absent. A
manifest-bound release now proposes stopped VM119 and one bounded no-retry V2b
boot, with fail-closed configuration validation and stop-and-retain recovery.
Twenty-five focused and 239 full adaptive tests pass. No remote file, ISO, VM or
boot was created; V1b/V2b await explicit execution approval.


### 2026-09-26 — V1b/V2b bootstrap gate passed

Jason approved the frozen V1b/V2b envelope. VM119 was created from a fresh import
and passed the stopped no-vNIC/no-agent validator. Its 376,832-byte seed ISO is
SHA-256 `af8278b6fe270f3a45651a376c426284d51a894fff1820173615f04051cd2ee5`.
One boot produced a 104,501-byte capture with one complete protocol envelope; the
strict parser accepted the expected run/manifest, 119 canonical bytes, result digest
and `interfaces=["lo"]`. The canary unit succeeded, no host stop or retry was
needed, VM119 is stopped, existing guests remain at baseline and no corpus ran.
V3 invented-fixture preparation is next; execution remains separately gated.


### 2026-09-26 — V3 invented-fixture release prepared

Implemented a deterministic local V3 renderer, ten-check semantic validator,
strict stopped-VM120 configuration gate, fresh-image creation script and one-boot
capture script. The fixture tests environment hygiene, unprivileged identity,
loopback-only topology, network-socket and fork denial, an inaccessible planted
canary, and read-only system paths. The reviewed unit requests private network,
syscall, filesystem and resource controls; the experiment exists to verify that
those requests are actually enforced rather than treating the unit text as proof.

Read-only Proxmox observations found `nextid=120` and retained VMs118/119 stopped.
Fifteen focused and254 full adaptive tests pass; shell syntax, cloud-config YAML and
release-manifest hashes validate. Release-manifest SHA-256 is
`f4d5b29491dafcd8393c290500da964084d5596de9943fae49b625ca854b0b6e`.
No remote staging, ISO, VM120, boot, corpus access, cleanup or push occurred. The
exact V3 window remains separately approval-gated and fail-closed.


### 2026-09-26 — V3 isolation fixture failed safely

Jason approved the frozen V3 scope. Remote staging hashes matched release manifest
`f4d5b29491dafcd8393c290500da964084d5596de9943fae49b625ca854b0b6e`.
The ISO is 380,928 bytes with SHA-256
`51cd876edbfaaaa0c6d328aced51e4aaaa47995030c5e3e39807adf11b576d2a`;
fresh stopped VM120 passed the exact no-vNIC/no-agent validator. One boot produced
a 105,156-byte capture, SHA-256
`11984e6a9cd19351a8d360c20f556d11db3c19c171879780b50c746e9e2ced86`.

Cloud-init reached `aster-s0-isolation.service`, which failed before emitting any
framed record. Strict parse result is `incomplete protocol`; no proposed isolation
check is credited. The guest powered off without host intervention, no retry or
corpus access occurred, and VMs118/119/120 remain stopped. A concurrent Proxmox
backup completed OK and explains transient container backup-lock changes. V4 is
NO-GO for accepted-corpus execution. Precise cause is UNKNOWN pending separately
approved read-only stopped-disk forensics.


### 2026-09-26 — V3 stopped-disk cause established

Jason approved the exact offline forensic scope. The reviewed script hash matched,
created a read-only loop, mounted ext4 `ro,noload,nosuid,nodev,noexec`, collected the
allowlist, then unmounted and detached successfully. The filesystem was clean and
the unit, probe and payload hashes matched the repository. `result.json` and
`protocol.txt` were absent.

Seven journal records prove systemd failed before Python with status
`226/NAMESPACE`: `/var/tmp/aster-s0-isolation-fixture-001` was not present while
setting up mount namespacing. The high-confidence design inference is that
`PrivateTmp=yes` replaced the service's `/var/tmp` view before `InaccessiblePaths=`
could mask the host-planted canary. The correction should retain `PrivateTmp` and
move the denial target outside `/tmp` and `/var/tmp`. No second boot, corpus access,
cleanup or push is authorized; the V4 decision remains NO-GO.


### 2026-09-26 — V3b correction frozen locally

Prepared a new immutable candidate rather than altering or rebooting VM120. The
single boundary correction retains `PrivateTmp=yes` and moves the planted canary
from private `/var/tmp` to `/srv/aster-s0-isolation-fixture-002`. All ten probes,
syscall filters, filesystem protections and resource bounds remain. New identities
are `isolation-fixture-002`, `aster-s0-isolation-fixture-002` and proposed VM121.

Nine focused and 263 full tests pass; shell parsing, cloud-config YAML and manifest
hash verification pass. Read-only preflight found next VMID121, the target paths
absent and memory/storage above gates. Release manifest SHA-256 is
`825d6d40cde3b1388484e37581473bb2c9c0d4e6e88d905406562536782fc4e1`.
Nothing was staged and no VM121/ISO/boot exists. V3b requires a new exact execution
approval; corpus access and push remain unauthorized.


### 2026-09-26 — V3b isolation boundary passed

Jason approved the exact V3b execution window. All staged hashes matched release
manifest `825d6d40cde3b1388484e37581473bb2c9c0d4e6e88d905406562536782fc4e1`.
The generated ISO is 380,928 bytes with SHA-256
`c8ad6005bfc221f522c4832208c6a869c936e5eddb885df4eab1f60375b07aae`;
fresh stopped VM121 passed the strict no-vNIC/no-agent configuration validator.

One offline boot produced a 104,695-byte capture with SHA-256
`5fbdb31fe58d9c2020bacca9953660dc137a5a3bbdbe081b0a83f056ecd65499`.
The strict parser accepted one complete envelope for `isolation-fixture-002`, exact
payload identity, 364 canonical bytes and result digest. The semantic validator
accepted all ten required isolation checks. The guest powered off without a host
stop; zero receipt-index mismatches were found; VMs118–121 are stopped. No retry,
accepted corpus, network device, credential, cleanup or unrelated VM mutation was
in scope.

The V4 boundary decision is GO for preparation of a fresh, separately reviewed
accepted-corpus candidate. It does not authorize corpus execution or establish
router quality, repeatability, scale or production suitability. The raw serial
capture remains on Proxmox because it contains noisy boot output and generated
public SSH host-key material; its bounded digest and sanitized decoded evidence are
retained in `run-v3b-isolation/`.


### 2026-09-26 — V5 accepted-corpus candidate frozen locally

Prepared the new-identity `corpus-descriptive-001` candidate after the V4 boundary
GO. It copies and pins the nine accepted 30-family pilot artifacts without running
the adapter or routers, and includes only the reviewed standard-library adapter,
router source and bounded worker. The comparison remains descriptive: three fixed
engines, two fixed profiles, 20 train/10 development, no tuning, model, cloud,
tool, credential or promotion path.

Proposed fresh VM122 keeps the proven no-vNIC/no-agent controls and adds exact
memory, CPU, task, file, unit and outer capture bounds. Nine focused and 272 full
adaptive tests pass; Python and shell syntax, cloud-config YAML and generated file
hashes validate. Read-only Proxmox preflight found `nextid=122`, VMs118–121 stopped,
new ISO/staging/release/run paths absent, the retained image exact and capacity
above gates. Release-manifest SHA-256 is
`1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.

No corpus evaluation, remote staging, ISO/VM creation, boot, cleanup or push
occurred. One exact stage/create/offline-boot/capture/stop-and-retain window needs
new human approval; low router agreement will be retained as a valid result and
will not trigger a retry.


### 2026-09-26 — V5 accepted-corpus attempt failed safely

Jason approved frozen release manifest
`1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.
All 23 staged files matched the candidate and release manifests. The generated
483,328-byte ISO has SHA-256
`f425e3bd7c330886d195a6d3e4d58b9a3950607c6ddb9d3103cbe58b4d0fa6fe`;
fresh stopped VM122 passed the exact configuration validator.

The one offline boot reached `aster-s0-corpus.service`, but the unit exited with an
error before publishing any framed record. The 104,662-byte serial capture has
SHA-256 `d8dc426db310dfe2855007da0edebc96170abcb293b997d76bcf65ea4c944aa8`.
Both receipt indexes verify with zero mismatches; strict parsing reports
`incomplete protocol`. The guest powered off without host intervention, VMs118–122
are stopped, and no retry occurred.

No routing metric is credited. Exact service cause and whether any accepted row was
read or partially processed are UNKNOWN pending separately approved read-only
stopped-disk forensics. The raw capture is not committed because it contains noisy
boot output and generated public SSH host-key material. A bounded forensic plan is
prepared locally; it authorizes nothing by itself.


### 2026-09-26 — V5 stopped-disk forensics established packaging cause

Jason approved the exact read-only VM122 inspection. The reviewed script mounted
the stopped disk through a read-only loop with journal replay disabled, exported
only the bounded allowlist, then unmounted and detached successfully. The
filesystem is clean; all 15 exact generated artifacts match, and `result.json` and
`protocol.txt` are absent. Corpus content was not exported.

Twelve journal records establish `ModuleNotFoundError: No module named
'validate_label_batch'` while importing `s0_descriptive.py`. Control flow proves
the entry point first read and SHA-256 verified all nine accepted corpus artifacts,
then failed before constructing JSON blobs, parsing accepted rows, adapting them,
loading or constructing an engine, or routing. The evidence classification is
therefore hash-verification-only, with zero accepted rows parsed, adapted or routed.

Systemd also reported `RuntimeMaxSec=` ineffective with `Type=oneshot`.
`TimeoutStartSec=75` and the host's 300-second capture bound remained active. Any
V5b candidate must package `validate_label_batch.py`, prove static import closure,
remove the ineffective directive, retain effective limits, use fresh identities,
and obtain a new exact approval. VM122 remains stopped; no retry, correction boot,
cleanup, promotion or push was authorized.


### 2026-09-26 — V5b packaging correction frozen locally

Prepared a fresh immutable candidate rather than altering or rebooting VM122. The
V5b bundle adds the omitted `validate_label_batch.py`, statically verifies every
imported sibling module is packaged, and proves the generated sources import under
the guest's `-I -S -B` Python flags. It removes `RuntimeMaxSec=75`, which the V5
journal proved ineffective for a oneshot unit, while retaining `LimitCPU=70`,
`TimeoutStartSec=75` and the outer 300-second capture limit.

The nine corpus artifacts and hashes, 20/10 split, engines, fixed 0.2 threshold,
profiles, result contract and all security controls are unchanged. Fresh identities
are `corpus-descriptive-002`, `aster-s0-corpus-002`,
`aster-s0-corpus-descriptive-002.iso` and proposed VM123. Nine focused tests pass
using only invented fixture rows; candidate/release hashes, cloud-config and shell
syntax validate. The available adaptive suite passes 274 tests; the existing
`test_full_aster.py` module was unavailable because this workstation runtime lacks
`httpx`, and no dependency was installed.

Read-only preflight found next ID 123, VM123 and every V5b path absent, VMs118–122
stopped, the retained image exact and capacity above gates. Release-manifest
SHA-256 is `721c377dccca4fef1a685427d85f791559f67686b8bbf533439589f88b3a5d0f`.
No accepted row was evaluated, and no staging, ISO, VM, boot, cleanup or push
occurred. V5b execution is a separate exact human gate.


### 2026-09-26 — V5b descriptive comparison completed

Jason approved the exact V5b manifest-bound VM123 window. The first archive stage
contained 30 macOS AppleDouble metadata files; exact-set validation stopped before
ISO or VM creation. Jason separately approved a script with SHA-256
`b395d369e2d1333ea7e2c3ece141872a61818348a8ef3fcb9a0ea81f2dd18c7a`.
It verified the complete unexpected set and every intended hash, deleted only the
30 metadata files and proved the exact 24-file stage.

Fresh VM123 passed stopped no-vNIC/no-agent validation. Its 491,520-byte ISO is
SHA-256 `2de12b7c2d5e10b0c36d298ac2a89d9fbb7dae304d2c6225fa561a79b8c08627`.
One offline boot produced a complete `corpus-descriptive-002` envelope. The strict
parser and result validator accepted 36,453 canonical bytes with SHA-256
`accfb55f825605451a6742e6aa5c25b0c52b40722915f2cc737f20342bec3198`.
The evaluator took 118,140,122 ns with 20.34 MiB peak RSS. The guest powered off;
no host stop or retry was required; VMs118–123 are stopped; both receipt sets have
zero hash mismatches.

Request-only complete counts on ten exposed dev families were 0/10 abstain, 4/10
keyword and 6/10 fixed nearest. Context-assisted counts were 0/10, 3/10 and 8/10.
Nearest had full coverage but still produced missing and extra capability errors.
Context yielded two nearest gains but one keyword loss. The hypotheses pass only as
descriptive finite-corpus statements. No confidence, privacy, production-locality,
cloud need or generalization claim is made.

The disposable VM took roughly 135 seconds end to end for 0.118 seconds evaluator
work. It remains an offline evidence boundary, not a serving harness. The result
retains all three engines as benchmark baselines and authorizes no router selection,
threshold tuning, policy change, permission change, cleanup or push. The S0
comparison is complete; M3 remains open for controlled harness and local-model
comparisons.


### 2026-09-26 — M3 serving-harness decision retains Aster

Read-only checks found the Aster and llama.cpp services active with zero systemd
restarts and the authenticated inference health endpoint healthy. Aster used about
44.6 MiB and llama.cpp about 9.55 GiB at the observation point. The deployed Aster
source, current worktree source and original controlled-comparison slice have three
different SHA-256 values; this prevents treating the earlier synthetic timings as a
fresh byte-for-byte benchmark of the live service.

The retained controlled evidence still answers the architecture question.
PydanticAI slim passed the preregistered overhead and conformance guardrails, but
added roughly 22 MiB peak RSS and measurable loop overhead without removing Aster's
deterministic validation or authorization boundary. Recorded Hermes configurations
remain much heavier in prompt and wall time. Existing Aster sysadmin, Home Assistant
and mirror graduations establish useful production local-model behavior, although
they are not comparative challenger runs.

The accepted ADR retains the bounded Aster Python runtime, treats Hermes as an
optional client/workflow harness, keeps PydanticAI as a probationary specialist
challenger, and defers LangGraph and Pi until a concrete requirement justifies them.
A live PydanticAI run is rejected for now because the offline evidence supplies no
benefit hypothesis worth adding provider integration, credential handling and load
to the single-slot model. The harness subdecision is complete. M3 remains open for
representative independently reviewed routing evidence; no framework, service,
permission, policy or production configuration changed.

Follow-up source archaeology resolved the apparent live-source uncertainty. The
read-only copy from LXC 104 is byte-identical to Aster source in commit `2c71d6b`
and the current local `origin/main` tracking tree. Its delta from the Stream A
worktree is ten lines of AI-PAM knowledge-source ranking and section anchoring.
The histories are 43 commits on each side beyond their merge base, so this task did
not merge them. Future live comparison must use the eventual reconciled intended
tree; this finding does not change the retain-Aster decision.


### 2026-09-26 — S1 representative holdout proposed

Repository review confirmed S0 cannot serve as M3's independent holdout. Its cases
were AI proposed, Jason saw proposed labels, and its development families are now
exposed. Resplitting or paraphrasing them would not remove suggestion anchoring or
test exposure.

The proposed S1 plan uses 50 new human-authored, no-suggestion families: five in
each of the ten required request strata, with fixed composition/constraint and
ambiguity quotas. It compares only abstain, unchanged keyword rules and fixed 0.2
nearest trained on S0 train rows. Confidence stays null. Predeclared shadow-entry
guardrails require 45/50 complete, no prohibited or invalid predictions, constraint
and ambiguity minima, no hard privacy/locality violation and CPU p95 below 25 ms.
Passing can only justify a separate read-only shadow proposal.

No case, label, helper, custody location, experiment or service was created by the
plan. S0 collection authority was capped and explicitly excluded a later study.
S1 therefore stops before collection and requires a concrete form/validator/custody
packet, then separate collection and evaluation approvals.


### 2026-09-26 — S1 pre-collection packet prepared

The packet now contains a blank form and bundle, frozen vocabulary, JSON Schema,
syntax-only validator, invented-fixture tests and a local custody design. Review
corrected the ambiguity gate from an impossible 8/10 to 4/5, defined the full
composition/non-plan subset as the denominator with an 80% rule, and removed an
unsupported privacy-routing claim because current engines do not output locality.

The initial `/private/tmp` draft proposal failed its backup exclusion check: Time
Machine reports that path included. The corrected current `$TMPDIR` parent is
excluded, outside all named repositories and absent; Spotlight is disabled. These
conditions must be rechecked at activation. An invented Git fixture survived a
disposable bundle/clone/hash restore, which does not prove HomeLab off-host backup.

Eighteen new S1 tests and 58 combined label/S0/S1 validation tests pass. Validator
core has no network, subprocess or file access and always returns collection and
evaluation authority false. The empty template is structurally incomplete. Manifest
SHA-256 is `93b9671b4a7c8e216fec00c1351499441e6e08a1aed50f765566645f3a578911`.
No draft path, human case, service, model call, evaluation or production change was
created. The packet is ready for an exact collection decision; push remains excluded.


### 2026-09-26 — S1 collection custody activated empty

Jason approved push and continuation. Forgejo and GitHub mirror refs both verified
at `a769867e5187b30e3b8ed52613119708bab29566`. The S1 packet and all artifact hashes
revalidated before the single draft directory was created.

The current per-user temporary child is mode `0700`; its 619-byte `bundle.json` is
mode `0600` and byte-identical to the approved empty template. Validation reports
zero cases/receipts, structurally not ready and no authority claims. No request,
label, timestamps or active effort were invented. Collection starts with Jason's
first request text; evaluation and another push remain excluded.


### 2026-09-28 — S1 first accepted timer batch

Jason supplied and accepted five sanitized timer/alarm requests, then completed a
human-authored label review in a local workbook. He self-reported ten active
labeling minutes and explicitly approved durable local-Git retention. The accepted
batch passed the syntax-only validator with five receipts, frozen plan/registry
hashes and no authority claims. It supplies five timer families and five
composition cases, but no adverse-constraint cases and no complete 50-family
corpus. It cannot be evaluated or used to promote a route.


### 2026-09-28 — S1 third accepted facts batch

Jason supplied and accepted five sanitized general-knowledge requests, completed
a local no-suggestion label workbook, self-reported five active labeling minutes,
and explicitly approved durable local-Git retention. He also explicitly approved
adding the validator-required `multi-capability` tag to each facts/web case. The
accepted batch passed the syntax-only validator with five receipts, frozen
plan/registry hashes and no authority claims. It supplies five facts families and
five facts/web composition cases, but no adverse-constraint cases and no complete
50-family corpus. It cannot be evaluated or used to promote a route.


### 2026-09-28 — S1 fourth accepted media batch

Jason supplied and accepted five sanitized media requests, completed a local
no-suggestion label workbook, self-reported five active labeling minutes, and
explicitly approved durable local-Git retention. He explicitly approved adding
the validator-required `multi-capability` tag to all five cases and changing the
one internal case's cloud class to `forbidden`. The accepted batch passed the
syntax-only validator with five receipts, frozen plan/registry hashes and no
authority claims. It supplies five media families and five media/home composition
cases, but no adverse-constraint cases and no complete 50-family corpus. It
cannot be evaluated or used to promote a route.


### 2026-09-28 — S1 second accepted household-control batch

Jason supplied and accepted five sanitized household-control requests, completed
a local no-suggestion label workbook, self-reported five active labeling minutes,
and explicitly approved durable local-Git retention. The batch passed the
syntax-only validator with five receipts, frozen plan/registry hashes and no
authority claims. It supplies five home families, including one home/media
composition case, but no adverse-constraint cases and no complete 50-family
corpus. It cannot be evaluated or used to promote a route.


### 2026-10-03 — S1 closed incomplete; SA3 corpus readiness started

The S1 manifest was reconciled across all nine accepted bundles without reading
or reproducing request text in the close-out record. It contains 45 accepted
families and receipts with 50 minutes of reported active labeling effort. The
human-accepted strata are uneven (web 1, mixed 4, ambiguous 3, personal 6 and
sysadmin 6), and no accepted case has an adverse-constraint tag. The frozen S1
protocol requires 50 cases, five per stratum and at least ten adverse-constraint
cases. Therefore S1 is closed as collection-feasibility evidence only. Its
accepted records, receipts and packet are preserved, while evaluation, routing
selection, training, calibration, shadow use and production promotion remain
blocked.

The successor task is local SA3 incident-corpus readiness. Repository review found
the intake manifest intentionally empty and the existing advisor slice explicitly
development-only. The empty intake contract was strengthened to require repair
scope, expected postcheck and latency protocol, matching the existing SA3
preregistration. This added no case, reviewer, model call, provider choice,
credential, network operation or production change. Unit tests cover the new
contract and hash-bound S1 close-out manifest.
