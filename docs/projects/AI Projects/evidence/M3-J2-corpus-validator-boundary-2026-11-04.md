# M3 J2 corpus-validator boundary — 2026-11-04

## Decision

**SOURCE READY; NO J2 CORPUS CREATED.**

The validator implements the preregistered 960-row boundary: exactly 768
training and 192 validation rows, balanced 48/12 across each of the 16 coherent
joint labels. It binds preregistration manifest `2abcd023…97ee`, the fixed
ontology, synthetic/preregistered metadata, the independent custodian identity
and no authority.

Every normalized request must be unique and disjoint from exactly eight
explicitly supplied exposed reference corpora. The content-free summary binds
the corpus, normalized text set, ontology and every reference digest/count,
while recording zero overlap and automatic routing off.

Five focused tests pass, including the valid 960-row shape and fail-closed
coverage for missing references, overlap, duplicates, label imbalance,
metadata/authority drift, duplicate JSON keys and malformed/duplicate reference
sets. No corpus text, label review, evaluation set, training, model call,
booking, route effect or deployment was created by this milestone.
