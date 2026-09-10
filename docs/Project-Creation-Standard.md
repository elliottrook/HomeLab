# HomeLab Project Creation Standard

> Status: Adopted repository process
>
> Owner: Jason
>
> Adopted: 2026-09-10

## Purpose

This document defines what Jason means by the **lab ethos**, the **usual
project template**, and the two available project authorization streams. It is
the default starting point whenever a HomeLab project is requested. A project
may tighten these rules but may not silently weaken them.

This repository process grants authority only where the active execution
environment, safety policy and access controls permit it. It does not bypass a
required platform approval or turn unavailable credentials into authority.

## The lab ethos

The HomeLab should be secure, private, understandable and recoverable while
remaining pleasant to use. Apply these principles in order:

1. **Protect people and data.** Avoid exposure, data loss, credential leakage
   and unexpected interruption before optimizing convenience.
2. **Maximum practical privacy.** Prefer local processing, private addressing,
   restricted identities and deliberate data collection. Do not send private
   material to a third party merely because doing so is easier.
3. **Least privilege and minimum change.** Use the narrowest identity, network
   path, permission, target and code/configuration change that completes the
   agreed outcome. Remove temporary access when its purpose ends.
4. **Usable security.** Controls must fit normal household operation and retain
   a documented administrative recovery path. A secure design that cannot be
   operated or recovered reliably is incomplete.
5. **Private by default.** Do not create public ingress, expose an admin
   interface, weaken a VLAN boundary or broaden a firewall rule unless the
   approved project explicitly requires and justifies it.
6. **Local-first, open and portable.** Prefer self-hosted services, open formats,
   standard protocols and exports that survive a product or model change.
7. **One declared authority for each fact.** Live state, NetBox, operational
   reference, project records, the human wiki and Aster's derived mirror have
   distinct roles. Report drift and conflicts; never resolve them silently.
8. **Evidence over assumption.** Inspect the actual deployed state, versions,
   dependencies and consumers. An exit code alone is not proof; validate the
   intended outcome and check for collateral effects.
9. **Reversible, incremental delivery.** Work in bounded milestones, preserve a
   known-good path, change one layer at a time where practical, and test rollback.
10. **Recovery is part of implementation.** Configuration, state, credentials
    and dependency order need appropriate protected coverage and a restore test.
11. **Observable operation.** Important services and failure modes belong in
    HomeLab Doctor and/or existing monitoring with useful, non-secret output.
12. **Documented operation.** Git records the design, decisions, commands or
    procedures worth retaining, evidence, accepted risk and final limitations.
13. **Production remains independent of automation.** Aster, a scheduled job or
    an AI session may assist operation but may not become an undocumented single
    point of failure.
14. **Stop on surprise.** A materially different topology, exposed secret,
    unknown destructive effect, failed recovery checkpoint or scope expansion
    triggers analysis before further state-changing work.

## Standard authorization common to all projects

Once Jason asks for a HomeLab project to be investigated or created, the
following work is pre-agreed within that project's scope and does not require a
separate conversational approval:

- inspect repository files, Git history and working-tree state;
- perform non-secret-bearing read-only checks of the named HomeLab systems;
- use established SSH access non-interactively with `BatchMode=yes` to known
  HomeLab targets for read-only discovery and validation;
- inspect service health, versions, resource use, topology, logs and sanitized
  configuration while avoiding commands or files likely to reveal secrets;
- create and edit project plans, documentation, tests and local code/config
  candidates in this repository;
- create synthetic, disposable test data when production data should not be
  changed, provided it is clearly labelled and cleaned up or retained as a
  fixture according to the project;
- run local and explicitly non-mutating remote tests;
- create local Git commits at the end of each completed milestone; and
- continue or resume the work after interruption using the project's persisted
  state and evidence.

Read-only authorization excludes credential stores, private keys, tokens,
password databases and commands known to print secret-bearing configuration.
If a configuration file mixes required facts and secrets, use a redacted query,
schema-restricted producer or source-local summary rather than reading the raw
file into an AI session.

SSH access is transport permission, not mutation permission. Its target,
identity and command must still comply with the selected project stream.

## Project authorization streams

Every new project must declare exactly one stream before implementation.

### Stream M — Monitored

Use for exploratory projects, unusually sensitive systems, or work where Jason
wants to approve each operational change.

- All common read-only and local planning work above is pre-agreed.
- Before each state-changing command or external write, present the exact
  target, intended change, expected effect, validation and rollback.
- Obtain approval immediately before that change.
- Group commands into one approval only when they implement one clearly bounded,
  reversible change and share the stated risk.
- A successful change does not authorize the next change.

### Stream A — Autonomous

Use only after Jason approves the project as autonomous with its scope, risks
and exclusions recorded in the project document.

- The approval covers the project's enumerated state changes from start through
  graduation, including unattended continuation after a session or usage-limit
  stop.
- Make only the minimal changes necessary to meet the recorded success criteria.
- Prefer staged, reversible and least-privilege changes; retain checkpoints and
  validate after each bounded change.
- Do not broaden scope merely because adjacent improvements are useful. Record
  them as follow-up projects or recommendations.
- Pause on a non-waivable stop condition below, a newly discovered material risk,
  or a required action outside the recorded scope.

Autonomous project approval does not grant general administrator authority. The
project must enumerate expected change classes, systems and exclusions well
enough that an independent reader can decide whether a proposed command is in
scope.

### Non-waivable stop conditions

Both streams require a new, explicit risk decision before:

- deleting or overwriting irreplaceable data, destroying a guest, wiping media,
  removing the last recovery copy or performing an untested irreversible action;
- revealing, exporting, rotating or invalidating a credential outside an exact
  approved credential task;
- creating public exposure, a new inbound Internet path or a materially broader
  firewall/trust rule than the approved design;
- weakening authentication, encryption, backup retention or network isolation;
- changing a materially different system, data set or objective from the
  approved project scope;
- proceeding after a backup/checkpoint cannot be verified where the next change
  depends on it; or
- accepting a risk whose likely blast radius or recovery path was not included
  in the pre-start assessment.

Product or execution-environment approval prompts remain mandatory even when a
repository project is Stream A. The agent should explain that this is a platform
control, not uncertainty about the project authorization.

## Remote Git and milestone records

Every completed milestone must end with:

1. validation of the milestone gate;
2. an evidence-log update in the project document;
3. relevant updates to operational and integration documentation;
4. a focused local commit with no unrelated user changes; and
5. synchronization to the configured Forgejo primary and GitHub protection
   remote when permitted.

Remote Git writes are externally visible mutations. The project document may
require them, but their execution must still follow the active repository and
platform approval rule. Under the current repository rule, obtain Jason's
explicit confirmation immediately before each push unless that exact push was
specifically authorized. If a push cannot occur, retain the local commit, record
the pending remote synchronization and continue only when doing so does not
compromise recovery or collaboration.

Never force-push, rewrite shared history, delete a remote branch, create a tag or
release, merge a pull request, or alter a remote workflow unless that exact
operation is within scope and separately permitted by the governing controls.

## Pre-start risk assessment

Before implementation, inspect the live and documented environment and present
a concise risk assessment to Jason. It must cover:

- objective, scope, exclusions and chosen authorization stream;
- affected systems, users, data, network paths and systems of record;
- current versions, dependencies and known consumers;
- confidentiality and secret-handling risks;
- availability, integrity, privacy and recovery risks;
- irreversible or destructive operations, including whether they can be avoided;
- expected authentication, firewall, DNS, storage and external-service changes;
- recovery checkpoint, rollback path and abort conditions;
- test strategy, including why synthetic/disposable data is or is not needed;
- likely service interruption and how it will be detected;
- backup, Doctor, monitoring, NetBox, wiki/mirror and documentation impacts; and
- unresolved decisions or risks requiring acceptance before work starts.

For Stream A, the assessment doubles as the authorization envelope. Work starts
only after Jason accepts it. For Stream M, it establishes scope but does not
replace the per-change approvals.

## Usual project document template

Create the project under `docs/projects/` and add it to
`docs/projects/README.md`. Use the following sections unless clearly irrelevant:

1. **Header** — title, status, owner, proposed/started/completed dates and Stream
   M or Stream A.
2. **Purpose and desired outcome** — the user-visible result, not merely the
   technology to install.
3. **Current state and evidence** — deployed versions, topology, dependencies,
   existing capabilities and known gaps.
4. **Scope and exclusions** — systems, data, allowed change classes and explicit
   non-goals.
5. **Authority model** — which source owns each relevant fact and configuration.
6. **Architecture and data flows** — identities, protocols, ports, storage and
   trust boundaries.
7. **Privacy and security design** — least privilege, credentials, data
   minimization, network policy, logging and public-exposure decision.
8. **Pre-start risk assessment** — risks, likelihood/impact, controls, residual
   risk, rollback and decisions accepted by Jason.
9. **Persistence plan** — checkpoints, idempotence, durable status and exact
   resume instructions.
10. **Milestones** — bounded implementation stages with prerequisites,
    checkboxes and measurable completion gates.
11. **Validation and evaluation** — functional, security, failure, regression,
    performance and user-workflow tests.
12. **Observability and maintenance** — Doctor/monitoring coverage, schedules,
    alert ownership, updates and staleness checks.
13. **Backup, restore and rollback** — protected components, retention, isolated
    restore proof and the last-known-good path.
14. **Documentation and systems-of-record updates** — the integration impact
    checklist below.
15. **Graduation criteria** — all gates, repeatability and accepted limitations.
16. **Evidence log** — dated action, evidence, result and any remaining risk.
17. **Close-out** — final architecture, ownership, recovery references and
    deliberately deferred work.

Checkboxes are evidence claims: mark one complete only after implementation,
validation and documentation are all true. A project remains proposed, ready,
active or pilot until its graduation gate passes.

## Required integration impact checklist

Every project must assess each item below and record either the required change
or **not applicable with reason**. Do not update a system merely to satisfy the
checklist when it is not an authority for the affected fact.

- [ ] **HomeLab Doctor** — availability, dependency, backup-age, drift or
  workflow check; use actionable non-secret output and test failure behavior.
- [ ] **Monitoring/alerting** — metrics, history, thresholds, notification owner
  and avoidance of duplicate/noisy checks.
- [ ] **Backup and recovery** — configuration, application state, databases,
  encryption material, source repositories and restore order.
- [ ] **NetBox** — device, VM, interface, IP, VLAN, rack, cable or service facts
  for which NetBox is the adopted authority.
- [ ] **Human wiki** — operator guidance, equipment/application page, manuals,
  dependencies and recovery links.
- [ ] **Aster mirror/snapshot** — derived salient knowledge, provenance,
  authority label and retrieval/evaluation updates; never treat it as authority.
- [ ] **Operational reference and runbooks** — current-state facts and safe
  procedures in `homelab-reference` or their successor.
- [ ] **Repository documentation** — architecture, addressing, network design,
  hardware inventory, operations, project portfolio and changelog as relevant.
- [ ] **Diagrams/rack records** — topology, power or physical-placement changes.
- [ ] **Homepage/service discovery** — useful private operator link and correct
  health behavior; no credentials embedded in dashboard configuration.
- [ ] **Authentication/authorization** — Authentik/native SSO, recovery login,
  service identities and least-privilege role mapping.
- [ ] **DNS, certificates and firewall** — narrow records/rules, split-DNS
  consistency, certificate renewal and rollback.
- [ ] **Automation and schedules** — systemd/cron/workflow ownership, missed-run
  behavior, concurrency control and observable last-success state.
- [ ] **Security inventory** — secrets kept outside Git, file ownership/modes,
  patch/update responsibility and temporary-access removal.

## Persistence and unattended continuation

Every project must survive a usage-limit stop, agent restart or lost interactive
session without relying on conversational memory.

- Keep the project document and evidence log current before a long-running or
  risky operation and at every milestone boundary.
- Record current milestone, completed steps, exact blockers, next safe action,
  validation state and rollback location in Git-tracked non-secret text.
- Store long-running job state in a durable, bounded state file or database with
  explicit schema/version; do not infer success from process absence.
- Make operations idempotent where possible. Detect already-completed work before
  replaying it.
- Use atomic candidate/accepted transitions and retain last-known-good state.
- Make partial output invisible to production consumers.
- Use bounded retries, timeouts and locks. A stopped run must fail safe and be
  resumable rather than starting over destructively.
- Never persist secrets, approval tokens or raw confidential output in the
  project log, Git, shell history or model-visible resume notes.
- On resume, re-read this standard, the project, repository status and live
  state; verify previous evidence before continuing.

## Validation and graduation baseline

In addition to project-specific tests, assess:

- expected function and the normal human workflow;
- least-privilege and deliberate denied-action tests;
- malformed, missing, stale and adversarial inputs;
- restart, reboot, timeout, interrupted-run and dependency-failure behavior;
- rollback to the prior accepted state;
- backup integrity and an isolated restore proportional to the change;
- secret-pattern and sensitive-output review;
- performance and capacity headroom;
- HomeLab Doctor and monitoring behavior in success and failure;
- regression of dependent services and existing Aster curricula; and
- two independent production-path passes for critical or AI-mediated behavior.

Synthetic data and disposable targets are preferred where a real failure would
risk production data. Synthetic evidence must be labelled, isolated from real
indexes and removed or retained intentionally as a test fixture.

A project graduates only when every required gate passes, recovery is proven,
documentation and systems of record agree, residual risks are accepted, normal
operation is supportable without the implementation agent, and no unexplained
temporary access or state remains.

## Project creation workflow

When Jason asks to create a project:

1. Read this standard, `AGENTS.md`, `docs/Standards.md`, the portfolio and all
   directly relevant project/operational records.
2. Inspect Git status and preserve unrelated user work.
3. Perform the pre-agreed read-only discovery needed to understand actual state.
4. Draft the project using the usual template and choose or request Stream M/A.
5. Present the pre-start risk assessment, meaningful alternatives and any hard
   decisions; avoid asking for permission for ordinary read-only discovery.
6. Add the project to the portfolio and changelog.
7. After Jason accepts the risk assessment and stream, execute milestone by
   milestone within the authorization envelope.
8. At each milestone gate: validate, update evidence and integrations, commit,
   and synchronize remotes when specifically permitted.
9. Persist a usable handoff whenever work may stop; resume from recorded state.
10. On graduation, run final regressions and recovery proof, record limitations,
    move the project to the completed-project location when appropriate, update
    all links, commit, and synchronize the accepted close-out.

## Exceptions

Any exception must be explicit in the project document with its reason, risk,
compensating control, owner and expiry/review point. Convenience alone is not a
sufficient reason. An exception applies only to that named project and does not
amend this standard.
