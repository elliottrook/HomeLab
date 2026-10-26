# M3 NLU narrow recognizer v1 development result — 2026-10-26

## Architecture

The rejected broad classifiers are replaced by an offline deterministic
challenger made from explicit recognizers for narrow request shapes:

- household device and timer commands with explicit targets;
- bounded lab and fixed Doctor reads;
- explicit calendar reads and public lookups;
- explicit service/package changes, still without authority;
- public factual questions;
- private-publication and backup-deletion denials; and
- impossible-request abstention.

Anything else, including missing referents and action-shaped advice questions,
returns `clarify` with no capability needs. The candidate emits only the six
fields of the existing interpretation classification boundary. It selects no
provider and cannot express authority.

## Development result

- exposed synthetic development cases: 24;
- exact six-dimensional matches: 24/24;
- focused recognizer and existing deterministic-guard tests: 14/14;
- adversarial checks cover unknown/referential requests, action-shaped advice,
  private publication, backup deletion and output-field confinement;
- automatic routing: disabled.

The system Python environment lacks the optional Pydantic dependency needed by
the broader historical benchmark module, so that unrelated suite was not
claimed here. Each exposed case was separately passed through the existing
dependency-free semantic validator.

## Limit

This is exposed development regression, not an independent quality estimate.
It did not read any private calibration or holdout case, call a model, select a
threshold, produce shadow traffic or change production. The next step is a
cross-set development challenge built only from already-spent development
corpora. A new independent calibration is justified only if this candidate
clears those exposed gates without unsafe false routes or privacy
underclassification.

