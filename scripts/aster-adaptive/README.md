# Aster Adaptive Computing — offline contracts and baseline slice

Offline M2–M4 experiments, not a production integration. The baseline runner uses
no service, model, broker socket, credentials, live report or application initializer.
Reuse the repository's existing Pydantic 2.13.4 dependency; the optional PydanticAI
comparison uses a separate disposable environment. Run from the repository root with Python 3.12:

```sh
/private/tmp/aster-lab-ops-venv/bin/python -m unittest discover -s scripts/aster-adaptive -p 'test_*.py'
/private/tmp/aster-lab-ops-venv/bin/python scripts/aster-adaptive/benchmark.py --output /private/tmp/aster-m2-rerun
```

`contracts.py` defines strict, immutable, extra-field-forbidding v1 records for
Capability, Decision, Harness Run, Outcome and Experiment, plus a filtered
Projection. JSON schemas are generated for interoperability; cross-record identity,
policy, expiry and DAG predicates require the Python validator too. JSON Schema
validation alone does not enforce those semantic constraints.

Catalogue declarations never grant permissions. `project_catalogue` filters using
an explicitly supplied trusted fixture permission set. Production grant data must
come from AI-PAM, which this adapter cannot contact. Fixture capability IDs do not
assert that similarly named live capabilities exist. All outcomes are synthetic,
quality is unevaluated, confidence/token counts are null, and promotion authority
is always none. Bounded opaque references are not a general-purpose redaction or
anonymization system; callers must supply non-secret references.

The adapter compiles only the named definitions of `select_tools`,
`normalized_messages`, `preload_read_only_context`, `build_payload`, the initial
TOOLS dictionary, TOOL_HINTS and ASTER_SYSTEM_PROMPT from the current local Aster
source. It does not import the application or run its initialization. Source hash
is bound to each run. Fixtures supply the executor, model name, timezone, persona,
response limits and disabled Lab Operations. This is deliberately a limited
source-slice measurement, not a parallel rewritten Aster runtime. It follows the
existing keyword preselection; it does not interpret or execute arbitrary DAGs.

Only four fixed tool implementations can appear in a contract. No shell, network
or effectful adapter exists. Prompt matching can narrow the planned capabilities
but cannot broaden them. Each fixture call checks scope, cancellation, expiry and
budget. Metadata excludes prompt/result content. Completed means payload built,
not plan success, correct answer or a completed external action. Instances are for
serial fixture use; no production threading/concurrency support is claimed.

The benchmark alternates direct-slice and validated-adapter order, discards ten
warmups and retains 200 timing samples per case as aggregates. Both paths include
JSON payload serialization. Source loading is measured separately. Peak RSS is
process-wide high-water usage. Bytes are not tokens. Network connections are
blocked during measurements and tests; fixed data is synthetic. No adoption
threshold or harness choice is inferred from these descriptive timings.

See the [M2 checkpoint](../../docs/projects/AI%20Projects/evidence/M2-offline-checkpoint.md)
for remaining gates and measured artifact provenance.

## Actual HTTP path and optional challenger

`test_full_aster.py` adds seven actual Aster ASGI chat-path checks, using synthetic
key authentication, fake readers/model, blocked connections and no startup workers.
Those checks brought the M2 suite to 26 tests. It does not require PydanticAI.

An optional hash-pinned temporary PydanticAI environment was used for the minimal
preload comparison. It is separate from the existing test/production environments:

```sh
PYDANTIC_AI_NO_BANNER=1 /private/tmp/aster-adaptive-pydanticai/bin/python scripts/aster-adaptive/candidate_checks.py
/private/tmp/aster-adaptive-pydanticai/bin/python scripts/aster-adaptive/compare_preload.py --mode aster --output /private/tmp/aster-preload-new.json
PYDANTIC_AI_NO_BANNER=1 /private/tmp/aster-adaptive-pydanticai/bin/python scripts/aster-adaptive/compare_preload.py --mode pydanticai --output /private/tmp/pydanticai-preload-new.json
```

The original four-case slice evidence remains immutable; new test files do not
retroactively change its measured implementation manifest. Compare current source
hashes and use new evidence paths for later runs. See the
[M3 result](../../docs/projects/AI%20Projects/evidence/M3-preload-results.md) and its
hashed dependency lock. The preload result retains Aster and is not a completed
M3 routing/tool-loop/model-quality comparison.

## Tool-loop and routing smoke runners

The isolated candidate environment runs both actual Aster chat-loop source and
PydanticAI against the same frozen eight-case tool script:

```sh
/private/tmp/aster-adaptive-pydanticai/bin/python scripts/aster-adaptive/compare_tool_loop.py --mode aster --output /private/tmp/aster-loop-new.json
PYDANTIC_AI_NO_BANNER=1 /private/tmp/aster-adaptive-pydanticai/bin/python scripts/aster-adaptive/compare_tool_loop.py --mode pydanticai --output /private/tmp/pydanticai-loop-new.json
python3 scripts/aster-adaptive/routing_smoke.py --output /private/tmp/routing-smoke-new.json
```

Routing is a separate dependency-free smoke comparison, not a production router.
Its 300 presentation variants represent 30 authored families, only ten in the test
split. No execution path exists and all outputs explicitly deny implied authority.
The negative challenger result is retained; do not tune against its test split.
See [tool-loop/routing results](../../docs/projects/AI%20Projects/evidence/M3-tool-loop-results.md).
Those checks brought the adaptive suite to 30 tests.

## Synthetic evidence storage

`evidence_store.py` stores strict experiment, outcome, evaluation and review
records in caller-owned SQLite files. Frozen experiment digests bind evaluations;
reviews reference the exact evaluation event and close further evaluation under
that experiment ID. No record can confer execution or promotion authority.

```sh
/private/tmp/aster-lab-ops-venv/bin/python scripts/aster-adaptive/evidence_demo.py --output /private/tmp/storage-proof-new.json
```

The demo creates and restores a disposable three-event ledger, then removes the
databases. It does not import or retrospectively preregister previous M3 results.
The current test suite has 40 tests. See the
[M4 checkpoint](../../docs/projects/AI%20Projects/evidence/M4-storage-checkpoint.md)
for recovery instructions and the limits of hash chains and reviewer metadata.

`Dataset`, `RegisteredRun` and `LinkedOutcome` add explicit lineage for new
measurements. A dataset manifest hashes synthetic inputs and expected labels;
registered runs bind its case IDs and the frozen experiment artifact. Linked
outcomes reference the exact run event. Legacy `outcome.v1` records remain readable
but do not carry this cross-record guarantee. There are now 45 adaptive tests.

```sh
/private/tmp/aster-lab-ops-venv/bin/python scripts/aster-adaptive/measure_lineage.py --output /private/tmp/lineage-proof-new.json
```

This runner refuses an existing output path, freezes its experiment before execution,
then retains four new fixture outcomes and restores the ten-event ledger. It records
no aggregate evaluation or reviewer decision. See the
[lineage checkpoint](../../docs/projects/AI%20Projects/evidence/M4-lineage-checkpoint.md).

`paired_evidence.py` adds a frozen protocol and an evaluation derived from exact
baseline/candidate outcome events. It requires complete case/repetition coverage,
rejects reused or omitted outcomes and counts families separately from repetitions.
Finalized paired experiments cannot accept further measurements. Legacy evaluation
records do not acquire this guarantee retroactively. The current suite has 52 tests.

```sh
/private/tmp/aster-lab-ops-venv/bin/python scripts/aster-adaptive/measure_paired.py --output /private/tmp/paired-proof-new.json
```

The paired runner excludes ledger I/O from timing and denies network connections.
It records no independent reviewer decision. See the
[paired checkpoint](../../docs/projects/AI%20Projects/evidence/M4-paired-checkpoint.md)
for measured results, exact scope and remaining live-use gates.

## Offline review of retained exports

`verify_evidence.py` reconstructs a bounded synthetic export in temporary storage
and recalculates paired totals without running measurement code. Supply an expected
head from independent custody; copying the candidate's own hash proves consistency
only. Pin and review the verifier code/dependencies before use. There are now 56 tests.

```sh
/private/tmp/aster-lab-ops-venv/bin/python scripts/aster-adaptive/verify_evidence.py /path/to/export.json --expected-head sha256:REPLACE_WITH_REVIEWER_RETAINED_HEAD
```

The verifier grants no review approval or measurement-authenticity claim. The
[storage and review design](../../docs/projects/AI%20Projects/M4-Storage-and-Review-Design.md)
defines the proposed ownership, retention and recovery boundaries; operational
acceptance and separate identities/custody have not been established.
