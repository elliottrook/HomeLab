# Aster Adaptive Computing — offline contracts and baseline slice

Local M2 scaffold, not a production integration or completed M2 gate. No service,
model, broker socket, credentials, live report or application initializer is used.
Reuse the repository's existing Pydantic 2.13.4 dependency; no PydanticAI or other
harness has been installed. Run from the repository root with Python 3.12:

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
The normal test command now runs 26 tests. It does not require PydanticAI.

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
The normal adaptive test command now runs 30 tests.
