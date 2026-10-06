# SA3 incident-corpus readiness discovery

Date: 2026-10-03  
Status: **ACTIVE LOCAL DISCOVERY; NO MODEL OR PROVIDER COMPARISON**

## Purpose

This is the first bounded successor task after S1 was closed incomplete. It
advances the programme's active operational-sysadmin path without creating human
labels or treating existing advisor prompts as an incident holdout.

The question is deliberately narrow: does the local intake contract contain the
fields that the SA3 preregistration requires before anyone can populate a
sanitized development or independently reviewed holdout incident manifest?

## Verified current state

- `sysadmin-sa3-development-manifest-v1.json` freezes twelve existing
  advisor/read-only cases as a **development regression slice**. It explicitly
  says it is not an incident corpus or independently reviewed holdout.
- `sysadmin-incident-intake-v1.json` is empty. It declares targets of 12
  development and 20 holdout incidents, with no case content, model input,
  reviewer identity or evaluation result.
- `SA3-evaluation-preregistration-2026-09-28.md` requires a future incident
  manifest to state repair scope when applicable, expected postcheck and a
  latency protocol in addition to the already-present symptom, observations,
  evidence-time, discriminating-check, permissible-outcome and forbidden-effect
  fields.

## Implemented local readiness improvement

The empty intake template now requires the three missing contract fields:
`repair_scope`, `expected_postcheck`, and `latency_protocol`. Its unit test
checks the complete required-field set and keeps the template empty. This is a
schema-level readiness change only; it adds neither case data nor a claim that
the eventual fields have been reviewed or are safe to execute.

## Remaining blockers

No populated incident corpus exists. Before an SA3 model/provider comparison, the
programme still needs:

1. 12 sanitized development incidents and at least 20 independently reviewed
   holdout variants, with each manifest field populated and immutable;
2. a reviewer/custodian and storage arrangement that keeps holdout answer labels
   out of model retrieval and implementation tuning;
3. a frozen settings, latency and scoring protocol; and
4. a separate authorization to run any Qwen or provider comparison.

The current change has no network, model, cloud, credential, tool, deployment or
production effect. It does not reopen S1 or make S1 material eligible for SA3.

## Follow-up local readiness improvement

The companion [custody readiness record](SA3-incident-corpus-custody-readiness-2026-10-03.md)
and its empty machine-readable template now make the split/answer-key boundary
explicit. They add no incident content or storage arrangement.

## Next safe action

Review the now-complete intake and custody templates and decide whether to
authorize a separately bounded, sanitized incident-corpus collection/custody
plan. Do not populate a case, run a model or select a provider merely from this
readiness record.
