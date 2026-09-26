# Local comparison implementation — fixture-tested candidate

Status: implemented and locally tested; **accepted-corpus execution disabled**.
Jason directly replied “approve” to implementation and fixture tests only, after
plan d89cdc9. No evaluation of the30 accepted cases, model calls or push authorized.

## Components

- `scripts/aster-adaptive/s0_descriptive.py`: bounded JSON/manual-evidence adapter,
  pinned full/per-case references, exact historical schemas, privacy/split checks,
  label-separated input preparation, scoring, aggregation and disagreement.
- `scripts/aster-adaptive/s0_descriptive_runner.py`: source-pinned existing rules
  and TF-IDF definitions, deterministic fixed-threshold comparison, timing and
  cooperative budgets. Only explicitly marked invented test fixtures are accepted.
  `require_live_readiness` always denies; no accepted-corpus CLI, file intake,
  output writer, Git operation, subprocess launcher or production adapter.
- `scripts/aster-adaptive/test_s0_descriptive.py`: disposable invented in-memory
  cases and schema receipts. Their actor strings test the schema, not actual
  human identity. Tests never read the accepted pilot records.

Historical original proposal pending flags are preserved and resolved only through
later hash-bound acceptance. The adapter does not manufacture authorization or
claim cryptographic authenticity. Model/collector/fixture-validator code unchanged.
Existing routing_smoke source is loaded from the exact checked bytes; its default
corpus-loading/threshold-tuning evaluate function is never called. No threshold fit.

## Validation

29 new tests pass; full adaptive suite125 passes in the pre-existing project venv.
Checks cover wrong pins/receipt/case hashes, missing acceptance, unknown fields,
nonfinite/oversized/duplicate JSON, expiry, changed revisions/splits, cross-split
exact request duplication, privacy inheritance, forbidden predictions, non-plan
capabilities, invalid output denominators, zero coverage, multiple accepted statuses,
input/label separation, deterministic ties, latency quantiles, wall/RSS/output limits,
engine exceptions and immutable inputs. A full invented30-case fixture pipeline
checks20train/10dev and300 warm observations per engine/profile; no pilot data used.

Network, subprocess and file-open attempts are denied during core comparison tests.
These monkeypatches are defense-in-depth tests, not an OS security boundary. Source
loading reads only the explicitly named pinned source. No hardware performance or
routing-quality result from these test fixtures is retained as pilot evidence.

## Material readiness limits

The plan's production-strength local isolation/launch requirements remain unverified.
`/usr/bin/sandbox-exec` exists on this Mac; existence is not proof that a restricted
launcher can run under the current Codex sandbox. No sandbox policy was installed,
a harmless nested sandbox probe was subsequently attempted with `/usr/bin/true`
and a deny-network/process-fork policy. It failed with exit71:
`sandbox-exec: sandbox_apply: Operation not permitted`. No accepted-corpus process
was launched. Do not bypass this environment restriction or weaken the plan.
A separately approved execution environment/launcher proposal is needed.

Wall/RSS checks are cooperative between pure function calls; a stuck engine is not
preempted and peak RSS is only observed, not a hard allocation limit. Output budget
is checked before return, with no file written; durable interrupted-run evidence,
atomic bounded output and duplicate-run prevention need the future launcher. Do not
claim these are complete merely because fixtures pass. Unknown/nonfinite resource
readings block usable output. No code path consumes approval booleans to enable a run.

The fixture guard prevents accidental current-corpus use, not deliberate code edits
or re-tagging by an administrator. Approval, reviewed pins and OS constraints must
remain separate controls. Plan runner/adapter/environment fields stay null and
status proposed-not-executable. Implementation hashes are recorded separately here;
filling the plan fields is not an approval mechanism.

## Next work and gate

Technical review passed for the initial26-test/122-suite implementation; three
additional local tests now bring counts to29/125 and add family-alignment checks.
No blocking defect was found in the fixture-only scope. Then prepare a concrete local launch design
with enforced network/process restrictions, parent-enforced timeout, bounded file
output, run identity and interruption evidence. Test those controls using fixtures
before presenting the exact frozen accepted-corpus run for Jason's execution approval.
No collection, labels, capabilities, runtime service or production policy changes.
Rollback: stop using this unlaunched candidate; retain source/test/evidence history.

Review-required follow-up must also bind an externally frozen root for plan/input/
source/adapter/runner/runtime hashes; caller-supplied recomputed manifests are not
independent trust. Enforce30/20/10 and aligned family IDs at any future live boundary.
The generic disagreement helper now rejects misaligned family IDs. Unique run IDs,
atomic bounded output and hard termination are future launcher requirements.

Final technical review independently reproduced29 focused /125 full passing tests,
verified all three current manifest hashes and clean diff checks, and approved a
local commit only. The failed sandbox probe remains a blocker; no corpus execution
or push is authorized.
