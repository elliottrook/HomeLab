# Offline contract reconciliation — 2026-09-26

Status: comparison complete; no schema migration, connected adoption or production
change. Owner: Jason. Both candidates remain separate offline tools.

## Exact inputs and reproduced evidence

Harness/evidence profile: `scripts/aster-adaptive` at local baseline `13f0a17`.
Selector profile: `services/aster-adaptive` and `schemas/aster` from immutable commit
`1a8fa680908eac8e0b7bb76845a0b1b061e593d7`. Extracted only committed files into
`/private/tmp/aster-contract-map-20260926`; the main checkout's unrelated edits were
not read as contract inputs or modified. A read-only Forgejo query returned
`2c71d6b12abcf3ed4d71aa9f9ea2af60a2fcfae2`; this newer operational baseline was not
merged during the isolated comparison. Recheck it before later integration.

The selector snapshot passes 29 tests and all 31 portable conformance vectors.
The harness/evidence profile passes 56 tests. Ten structural sample checks (five
contract families in each direction) accept their native representation and reject
the other profile. [Wire result](M2-contract-map/wire-comparison.json),
[selector conformance](M2-contract-map/selector-conformance.json) and
[manifest](M2-contract-map/manifest.json) retain exact provenance. This small sample
check is not an exhaustive proof of disjoint languages or semantic equivalence.

The first comparison attempt failed before producing evidence because the dynamic
module loader had not registered its module for postponed type resolution. Registering
the pinned module before import fixed the harness; no contract or expected outcome
was changed. Network connection attempts were blocked during comparison.

## Mapping and non-equivalence

| Concept | Harness/evidence profile | Selector profile | Integration rule |
|---|---|---|---|
| Capability | Four literal fixture tools; permission references, fixture-only locality and no effects | Broader source-derived catalogue; declared read/proposal effect, sensitivity, execution disabled | Neither grants authority; do not translate declared read effect into permission |
| Eligibility | Explicit fixture grants filtered into Projection; principal/policy/registry/expiry bound in HarnessRun | Fixture-filtered Catalogue digest bound to request and decision | Preserve exact projection plus trusted provenance; no client-created catalogue can authorize |
| Request/decision | Principal and expiry; answer/plan/deny etc.; null confidence | Separate DecisionRequest binds source engine, content handle, sensitivity/deadline; null probability | Preserve source identity and all constraints; statuses need explicit semantic mapping |
| No selected tool | `answer` may build a model payload in a fake no-model context | `abstain` means selector abstained, not that assistant refused to answer | Never equate the two labels without scope |
| Harness run | Nested decision/projection/budgets; simulated fixture execution | Selection-only observation; tool/model calls always zero; decision digest | Keep selection observations distinct from execution observations |
| Outcome | Completion/denial/cancel/expiry/budget state, fixture calls, elapsed ms, bytes | Selection result, label provenance and route correctness; no execution | Do not invent tool counts, successful actions or labels during conversion |
| Experiment | Frozen spec and linked dataset/run/outcome/paired-evaluation ledger | Explicit hypothesis, reviewed source pin and selector-conformance result | Keep independent preregistration and source pins; do not import historical results as newly preregistered |
| Digests/identifiers | `sha256:` prefix; broader bounded opaque refs | Bare hex digests; narrower lowercase identifiers | An encoding conversion is not provenance verification or authorization |
| Version strings | `capability.v1`, `decision.v1`, `outcome.v1`, `experiment.v1` | Same strings for incompatible records | Version alone is ambiguous; a future interface must bind a profile and exact schema digest |
| Execution source | Extracted reviewed source slice; actual digest bound to run, but existing runner can derive that digest from current source | Separate definition pins expected source before selector compilation | Carry the independent expected-source check into any unified runner; do not accept current source merely because it hashed successfully |
| Semantic validation | DAG, principal/projection, budgets and expiry; executor rechecks | DAG, request/policy/registry/engine, eligibility, expiry and step bound | JSON Schema alone is insufficient in either profile |

Both use strict extra-field denial and synthetic fixtures. Both are local Python
implementations, not independent cross-language validators or security sandboxes.
AST extraction executes selected trusted code and is not safe for arbitrary source.
Neither profile's syntactically valid record grants broker authority.

## Decision and next bounded implementation

Retain both tools for their existing purposes. Do not rename historical schema
versions or rewrite retained evidence. Do not add a permissive auto-detecting converter.
Before a shared interface is adopted, define a new explicit profile/namespace and
schema digest, preserve unsupported fields by rejecting conversion, and use both
conformance sets plus cross-record cases. A connected proposal must still reauthorize
through the approved AI-PAM path; M1 Stage2 remains a dependency.

The next useful local correction is independent source pinning in the fixture harness:
require a reviewed expected digest before compilation/measurement, record expected
and observed values separately, and test drift denial before executing extracted
code. Existing measured artifacts remain historical. Do not rerun timing comparisons
just to make the two schema families appear interchangeable.

M4 review/custody and M3 representative/model gates remain open. This comparison
needs no new dependency, service, credentials, private data, inventory change or
network route. It introduces no authority and performs no push. The temporary
snapshot is reproducible from the pinned commit and is not an operational dependency.
