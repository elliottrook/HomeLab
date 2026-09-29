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

## Required roles

Before activation, Jason designates named people for all three roles:

| Role | Required separation |
|---|---|
| Holdout custodian | Keeps raw candidate text, accepted sanitized case content, and labels outside the repository and the Aster knowledge corpus. |
| Independent reviewer | Is not the author of the case and is not the person tuning the evaluated model; approves privacy, causality, rubric, and label before release. |
| Evaluation operator | Receives only the fixed evaluation bundle for a run and cannot edit cases, labels, or the manifest after its release digest is recorded. |

One person may not hold all three roles. If a suitable independent reviewer is
not available, do not claim an independent holdout; record the limitation and
retain development-only evaluation.

## Proposed custody workflow

1. Create no files until Jason authorizes collection and names the custodian and
   reviewer.
2. Use a new owner-only scratch directory beneath `$TMPDIR`, proposed as
   `${TMPDIR%/}/aster-sa3-holdout-drafts`, with directory mode `0700` and files
   mode `0600`. The activation check must reject symlinks, foreign ownership,
   broader permissions, a path inside any repository, backup inclusion, search
   indexing, or Aster knowledge/mirror inclusion.
3. The custodian authors a sanitized candidate with no credentials, identifiers,
   internal addresses, raw logs, copied private conversations, or repair
   commands. The candidate records its source category, evidence age policy,
   allowed observations, expected discriminating checks, permitted outcome,
   forbidden effects, latency protocol, and a causality-separation note.
4. The independent reviewer accepts or rejects the exact case and label. The
   custodian records a canonical-content hash and a separate label hash. Rejected
   text is deleted; retain only a content-free count and reason code.
5. Before any model run, freeze a 20-case release manifest containing case IDs,
   split, family, case hash, label hash, reviewer receipt hash, release digest,
   evaluator version, and latency protocol. It contains no case text or labels.
6. The evaluation operator receives the fixed bundle through a reviewed local
   handoff. Results record case ID, digest, timing, tool/effect audit, outcome,
   and uncertainty without copying private evidence into Git.
7. Git may retain only the content-free release manifest, aggregate evaluation
   results, and reviewer receipt hashes after a local review. A remote push
   remains separately authorized.

## Activation gates

Activation requires all of the following before a single case is authored:

- Jason names the custodian, independent reviewer, and evaluation operator.
- A read-only exclusion check verifies the exact scratch path, ownership, mode,
  repository separation, backup behavior, indexing state, and absence from Aster
  sources.
- A fixed sanitization checklist and reviewer form are approved.
- The source/variant separation rule is demonstrated against the completed
  development intake without disclosing new holdout content.
- Retention, withdrawal, and private-data incident handling are accepted.

## Retention and failure handling

- Unaccepted drafts are deleted at rejection or after seven days.
- Accepted holdout content and labels remain with the custodian and are reviewed
  at 30 and 90 days; Git retains only content-free digests and receipts.
- On a secret/private-data incident, stop authoring, do not stage or publish the
  material, delete the draft, record a content-free incident fact, and reassess
  custody.
- If custody, reviewer separation, or bundle integrity cannot be demonstrated,
  do not run the holdout. Report SA3 as incomplete rather than substituting
  development scores.
