# SA3 holdout custody plan

Date: 2026-09-28  
Status: **proposed and unactivated; no holdout case, label, directory, service, or model run exists**

## Purpose and boundary

SA3 requires at least 20 independently reviewed held-out incident variants.
The completed 12-case development intake is exposed to implementation work and
cannot be relabeled as this holdout. This plan defines custody before any
holdout authoring. It does not authorize collection, model evaluation, a Qwen
configuration change, cloud egress, tool use, or deployment.

Each holdout must use a later or causally changed incident variant. It must not
reuse a development case's answer sequence, sanitized observation bundle, or
label. A related family is allowed only when the new variant is demonstrably
independent from the development case.

## Solo-lab procedural independence

This is Jason's personal lab. Requiring three unrelated humans would make the
holdout impractical without materially improving safe day-to-day operation. The
holdout therefore uses **procedural independence**, not external human
independence: separate, fresh GPT/Codex sessions perform distinct roles under
fixed access rules, and Jason remains the sole policy owner and final authority.

This design supports a meaningful anti-contamination check for a personal lab.
It must not be described as third-party audit, external validation, or proof of
universal model reliability.

Before activation, Jason names or starts a separate session for each role:

| Role | Required separation |
|---|---|
| Custodian session | Creates candidate case content and labels from approved sources; keeps them outside the repository and Aster knowledge corpus; does not inspect model runs or edit the evaluated implementation. |
| Review session | Receives the candidate and rubric, but not the implementation workspace, development answer sequence, or model results; checks privacy, causality, rubric, and label consistency. |
| Evaluation session | Receives only a fixed release bundle for the run, with labels withheld; cannot edit the cases, labels, or manifest after the release digest is recorded. |
| Scoring session | Receives the fixed run record and labels only after the run digest is sealed; cannot edit the evaluated implementation or rerun selected cases. |

The same GPT/Codex conversation must not perform more than one of these roles
for a release. Sessions use separate task histories and separate local
directories. Jason may inspect all artifacts and approves every transition, but
does not need to recruit an organization or external reviewer.

## Proposed custody workflow

1. Create no files until Jason authorizes collection and names the custodian and
   reviewer.
2. Use a new owner-only scratch directory beneath `$TMPDIR`, proposed as
   `${TMPDIR%/}/aster-sa3-holdout-drafts`, with directory mode `0700` and files
   mode `0600`. The activation check must reject symlinks, foreign ownership,
   broader permissions, a path inside any repository, backup inclusion, search
   indexing, or Aster knowledge/mirror inclusion.
3. The custodian session authors a sanitized candidate with no credentials, identifiers,
   internal addresses, raw logs, copied private conversations, or repair
   commands. The candidate records its source category, evidence age policy,
   allowed observations, expected discriminating checks, permitted outcome,
   forbidden effects, latency protocol, and a causality-separation note.
4. The review session accepts or rejects the exact case and label. The
   custodian records a canonical-content hash and a separate label hash. Rejected
   text is deleted; retain only a content-free count and reason code.
5. Before any model run, freeze a 20-case release manifest containing case IDs,
   split, family, case hash, label hash, reviewer receipt hash, release digest,
   evaluator version, and latency protocol. It contains no case text or labels.
6. The evaluation session receives the fixed bundle through a reviewed local
   handoff with labels withheld. The scoring session receives the label bundle
   only after the evaluation digest is sealed. Results record case ID, digest,
   timing, tool/effect audit, outcome, and uncertainty without copying private
   evidence into Git.
7. Git may retain only the content-free release manifest, aggregate evaluation
   results, and reviewer receipt hashes after a local review. A remote push
   remains separately authorized.

## Activation gates

Activation requires all of the following before a single case is authored:

- Jason designates separate custodian, review, evaluation, and scoring sessions.
- A read-only exclusion check verifies the exact scratch path, ownership, mode,
  repository separation, backup behavior, indexing state, and absence from Aster
  sources.
- A fixed sanitization checklist and reviewer form are approved.
- The source/variant separation rule is demonstrated against the completed
  development intake without disclosing new holdout content.
- Retention, withdrawal, and private-data incident handling are accepted.

## Local handoff validator

`services/aster-agent/evals/validate_sa3_holdout_release.py` validates a
content-free handoff manifest. The accompanying template contains no sessions,
cases, labels, or digest. A sealed manifest requires exactly 20 unique case IDs,
four distinct session receipts, three SHA-256 receipts per case (case, label,
and review), and a canonical release digest. It rejects case text, labels,
symptoms, evidence, prompts, and responses as manifest fields.

## Retention and failure handling

- Unaccepted drafts are deleted at rejection or after seven days.
- Accepted holdout content and labels remain with the custodian and are reviewed
  at 30 and 90 days; Git retains only content-free digests and receipts.
- On a secret/private-data incident, stop authoring, do not stage or publish the
  material, delete the draft, record a content-free incident fact, and reassess
  custody.
- If session separation or bundle integrity cannot be demonstrated, do not run
  the holdout. Report SA3 as incomplete rather than substituting development
  scores.

## Content-free procedural rehearsal

On 2026-09-28, separate fresh GPT/Codex sessions rehearsed the four roles using
one temporary, fully generic authorization-state scenario. The custodian drafted
it, the review session required a stricter rubric, the evaluation session saw no
label, and the scoring session rejected the output because it omitted required
evidence and proposed a different verification. No case text, label, bundle,
hash, model configuration, latency measurement, or source data was retained.
No lab system was accessed or changed.

This confirms the role handoff can reject an insufficient answer in a solo-lab
workflow. It is not a holdout case, does not count toward the 20-case target,
and provides no Qwen/provider performance claim.
