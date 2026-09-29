# SA3 development-source queue

Date: 2026-09-28  
Status: **planning inventory; not incident cases and not a holdout**

## Purpose

The SA3 intake requires twelve source-referenced development incidents. Two are
reviewed in `services/aster-agent/evals/sysadmin-incident-intake-v1.json`.
This queue identifies bounded, repository-recorded starting points for further
case authoring and makes gaps explicit. It does not copy raw logs, reconstruct
an answer key, create a case, or authorize collection, evaluation, reasoning,
tool use, or deployment.

## Reviewed cases already recorded

| Intake ID | Source | State |
|---|---|---|
| `video_archiver_jellyfin_verification` | `Video-Archiver-Repair-2026-09-28` | Jason-approved development case |
| `paperless_ip_collision` | `Paperless-IP-Collision` | Jason-approved development case |

## Candidate source records

Each candidate requires a separate sanitized scenario, label, reviewer decision,
and source check before it enters the intake. A source may inform a development
case but must not be reused as an answer key or relabeled as a holdout.

| Family | Repository source | Candidate boundary |
|---|---|---|
| ARR second login | `docs/runbooks/ARR-SSO-Repair-2026-09-27.md` at `c4afd8b` | Diagnose a supported authorization/header mismatch from sanitized status evidence; no login, credential, proxy, or ARR mutation. |
| Doctor parser/schema crash | `docs/runbooks/Lab-Health-Review-2026-09-27.md` at `a05047a` | Separate malformed/empty report handling from a target failure; no Doctor, service, or broker change. |
| B60 software rendering | `docs/projects/B60-Inference-Engineering.md` and `scripts/b60-inference/README.md` at `127eb08` | Interpret retained capability evidence; no model, kernel, driver, or service change. |
| DNS asymmetry | `docs/Current-Network-Baseline.md` at `c6c0191` | Distinguish routing/interface evidence from name-resolution symptoms; no address, route, DNS, or firewall change. |
| Missing backup configuration | `docs/runbooks/Backup-Coverage-Audit-2026-09-26.md` at `83e0901` | Evaluate retained coverage evidence; no backup schedule, retention, or storage mutation. |
| Interrupted backup | `docs/runbooks/Backup-Coverage-Audit-2026-09-26.md` at `83e0901` | Evaluate retained interruption and recovery-order evidence; no backup schedule, retention, or storage mutation. |
| Empty Doctor inventory | `scripts/doctor.sh` at `55a73c3` | Distinguish an empty collection from a shell/parser failure; no script or target change. |
| B60 preflight/rollback | `scripts/b60-inference/guard.py` and README at `b62a6d3` | Interpret a failed preflight and correct abstention/rollback advice; no benchmark, package, or hardware action. |
| Stale inventory | `docs/projects/Backup-Synology-Decommission.md` at `816b544` | Distinguish stale offline claims from current retained inventory evidence; no backup, device, or inventory mutation. |

## Explicit gaps

The earlier preregistration wording compressed **missing backup configuration**
and **interrupted backup** into one phrase. The controlling Operational Sysadmin
Capability specification keeps them as two of the twelve coverage labels, and
this queue now does the same. Several labels also overlap the two reviewed
sources: Jellyfin authentication and copied-audio budgeting are part of the
reviewed Video Archiver/Jellyfin history; ambiguous ownership is part of the
reviewed Paperless collision. They must not be counted again without a causally
distinct, sanitized source record.

`NetBox guest-reboot startup` still lacks a clearly identified incident source
in this audit. A future case needs a newly selected source record with its own
sanitized evidence and review; it must not be invented to fill the target.

The next review packet should select at most one distinct source per proposed
case, state its retained observation bounds and forbidden effects, and keep the
twenty-case holdout in separate custody.
