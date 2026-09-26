# Offline adaptive contract candidate

No deployed service. No credentials, tool execution, model call, network client,
production catalogue fetch or raw interaction collection. Uses the **existing**
local Python3.12/Pydantic2.13.4 environment; no dependency was installed.

```sh
/private/tmp/aster-lab-ops-venv/bin/python -m unittest discover -s services/aster-adaptive -p 'test_*.py'
/private/tmp/aster-lab-ops-venv/bin/python services/aster-adaptive/evaluate.py --output /private/tmp/m2-result.json --schemas /private/tmp/m2-schemas
```

The repository schemas in `schemas/aster` are exported JSON Schema2020-12 from
strict models in `contracts.py`. The JSON wire representation is the contract;
Pydantic is an interchangeable validator implementation. This is a **candidate
v1**, not a published stable interface. Before connecting any runtime, review
schema and semantic conformance, version changes and authorized catalogue access.
Unknown fields/versions fail. Cross-record policy/registry binding, expiry,
known-capability and graph invariants are enforced in Python and require equivalent
semantic validation in another implementation; JSON Schema alone is insufficient.

`baseline.py` reads a trusted, digest-pinned repository source file and extracts
only its literal regex declarations and pure `select_tools` function. It does not
import Aster or run application initialization. The extracted function is executed
Python, not a sandbox for arbitrary source: use only the reviewed local source.
`experiment-definition.json` independently pins the reviewed baseline source.
`evaluate.py` rejects source drift before selection and records the expected and
measured digests separately, alongside candidate and definition provenance.
The pin must change only through a reviewed experiment revision, never by accepting
whatever source the evaluator happens to read.
It extracts actual input schemas; output schemas remain explicitly opaque because
no tools execute. This is a selector adapter, not a complete harness replacement.

The fixture catalogue is a scoped *eligibility projection*, never an authority.
All entries have execution disabled. Each request uses a recorded policy-filtered fixture catalogue; its digest is
bound in both request and decision. Validation rejects steps outside that exact
projection. The request also binds the expected baseline engine digest. A future trusted adapter must obtain a policy-filtered projection
and reauthorize every effect through AI-PAM; client-controlled IDs, catalogue
membership and a valid plan cannot grant authority. M1 must graduate before a
connected pilot relies on that path.

`fixtures.json` deliberately separates existing expected tools from desired
capabilities. Expected outputs test baseline preservation, not gold routing
quality. Desired capabilities are design labels awaiting human adjudication and
are not silently added to the registry. A no-tool selection means model-only
fallback in the existing harness, not necessarily abstention from answering.
The offline adapter names it `abstain` only within its tool-selection task.

Plans are selection-only: no parameters, shell, tool arguments/results or DAG
execution. Confidence is always null. Data egress, tools, model calls and cost are
zero; these claims are scoped to this offline adapter. Synthetic time starts at1
for reproducibility; emitted plans are not current authorizations. Registry/policy
mismatch, expiry, unknown capabilities, graph cycles, oversized input, extra
secret fields, deadlines and step bounds reject or abstain without executing.

Metrics measure warm, single-process local selector/contract CPU overhead. They
do not measure model tokens, inference queueing, live harness latency, network
cost, workload routing quality, calibration, or deployed resource contention.
Tests deny socket/process creation during the evaluator. Allowed string fields
are not a universal secret detector: production ingestion needs a reviewed
privacy boundary and must never log model validation errors with raw input.

Rollback is removal of this unused directory and candidate schemas/evidence
pointers; retain historical evidence. No service restart or infrastructure restore
is required. No auto-promotion or permission change exists.
