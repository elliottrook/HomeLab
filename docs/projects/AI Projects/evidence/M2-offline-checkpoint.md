# M2 — offline contracts and Aster baseline slice

Date: 2026-09-25. Status: **M2 started; offline scaffold verified; full gate open**.

## Publication and current scope

Jason requested “Push and move on.” The M1 checkpoint `a5e8b22` was merged locally
with non-overlapping Forgejo B60 updates through `08b225a`, producing `35175c8`.
The authorized push advanced Forgejo main to
`35175c8c6df1db38e3e7fd4f4859d40097665e55`; a read-only query verified GitHub main
at exactly the same hash. No direct GitHub push or production deployment occurred.
The M1 evidence file's original pending-publication statement is now historical.
M1 security review, trust separation and deployment gates remain open.

M2 proceeded independently with local synthetic contracts and controlled baseline
measurement. No broker/runtime deployment, personal collection, inference call,
new dependency installation or new service was required.

## Deliverables and validation

- Strict Pydantic 2.13.4 contracts for Decision, Harness Run, Capability, Outcome
  and Experiment, with generated JSON schemas. A supplementary projection binds
  fixture principal, policy, registry and expiry. Extra/nested raw fields fail
  validation; plans cannot imply authority or uncalibrated confidence.
- Minimal four-item fixture catalogue: time, HA, Forgejo and NetBox report reads.
  Explicit trusted permission filtering produces projections; these records are
  not a second production permission registry.
- An adapter executes the current Aster source's payload-building function slice
  with fixed synthetic executor results. AST extraction skips application imports,
  setup, environment credential reads and real readers. It is not the complete
  production harness, authenticated ingress or broker integration.
- Nineteen conformance tests pass: version/field rejection, nested sensitive-field
  rejection, principal/policy/registry binding, unknown/ungranted capabilities,
  expiry, call/output/time budgets, DAG validity, duplicate catalogue entries,
  no implicit grants, no promotion authority, source drift, cancellation, prompt
  scope expansion and unchecked-object revalidation. Network connect is prohibited.
- Four fixed cases, 200 retained paired timing samples each after ten warmups;
  twenty separate source-slice load measurements. Full manifests, schema exports,
  catalogue and measured experiment record are in [M2-offline](M2-offline/baseline.json).

| Case | Direct slice median ms | Validated adapter median ms | Adapter p95 ms |
|---|---:|---:|---:|
| No tool | 0.0172 | 0.0267 | 0.0292 |
| One read | 0.0173 | 0.0306 | 0.0334 |
| Two reads | 0.0222 | 0.0380 | 0.0406 |
| HA read | 0.0228 | 0.0359 | 0.0385 |

These are descriptive Mac measurements, not model performance, statistical
noninferiority, production latency or evidence that one framework is better.
Token counts remain null. No answer is generated and no answer-quality claim is
made. Serialized payload bytes include Aster's actual system prompt with fixture
persona/context; those payload contents are not retained in the evidence output.
The underlying Aster source SHA-256 is
`8777687ce97055d2db3254aa6b30ddf37fc61e73dac2bd18008cbea3fef1a8b6`.
Evaluator, adapter, contracts, fixture and test digests are recorded in baseline.json.

## Limits and next safe action

1. Full M2 remains open: review these provisional contracts, pin a complete runtime
   manifest and validate the full Aster adapter path in an isolated configuration.
   The slice excludes HTTP ingress, authentication, Lab Operations, model execution,
   streaming, retries and real source readers. Its overrides are fixture values,
   not observed live configuration. Do not mark M2 complete from this microbenchmark.
2. The generic v1 shape is intentionally narrow: fixture-only locality, synthetic
   metadata, zero model calls and four tools. Later adapters require explicit
   schema/version review; do not silently widen v1 or repurpose fixtures as grants.
3. Define contract compatibility and the minimal PydanticAI comparison before M3.
   Start with existing Aster versus minimal PydanticAI, retaining the fixed corpus
   and separate conformance checks. LangGraph requires a demonstrated workflow need.
   Do not install major frameworks merely to fill a comparison table.
4. Prepare a bounded read-only runtime manifest/headroom check independently of the
   B60 Stream M programme. Current inference build/settings and production
   performance remain unverified by this local run.
5. Keep the M1 independent review and Aster approval trust-base gate visible. No
   connected pilot relies on the published but undeployed correction.

Run commands and implementation limits are in the
[offline runner README](../../../../scripts/aster-adaptive/README.md).
A rerun should write to a fresh output directory, compare source/dataset digests
first and retain a new evidence version rather than overwrite an accepted result.
No production rollback or systems-of-record update is needed for these offline
files. Removing the optional scaffold leaves existing production code unchanged.
M2 publication is separate from the already completed M1 push and needs its own
explicit remote-write authorization.
