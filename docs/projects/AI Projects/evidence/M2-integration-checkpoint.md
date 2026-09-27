# M2 — integration checks and runtime reconciliation

Date: 2026-09-25. **Offline M2 contracts/baseline gate complete. Production
integration and M1 security gates remain open.** This completion covers the
approved synthetic foundation profile, not all future workflows or model-serving
performance. The prior M2-offline checkpoint remains the historical first stage.

## Gate evidence

| M2 requirement | Evidence |
|---|---|
| Five versioned contract families | M2-offline schema exports and `contracts.py`; strict Python cross-record validation |
| Minimal authorized catalogue projection | Four fixture capabilities; explicit fixture permissions; unknown or unprojected capabilities denied; no live entitlement duplicated |
| Current Aster baseline adapter | Exact source slice plus actual application HTTP chat tests with fixture dependencies; source hash matches live Aster |
| No execution through unknown capabilities | Contract rejection, prompt scope tests, actual HTTP unsolicited-model-call denial |
| No leaked secret fields | Extra/nested content fields rejected; fixture authentication value absent from model payload; no real credentials used |
| No behavior or authority expansion | Production application source unchanged; all additions are optional offline code and evidence |
| Baseline overhead measured | Four cases × 200 retained paired samples in M2-offline; actual HTTP path separately validated, not conflated with slice timing |

**26 adaptive tests pass**, including seven new actual-application HTTP integration
tests. **89 existing Aster tests pass** unchanged. The HTTP tests exercise real
middleware, synthetic API-key authentication, persona/conversation filtering,
preload/payload construction, bounded chat loop and progress-stream error framing.
Readers and upstream generation are fixed test doubles. Missing/wrong identity
fails before any reader/model fixture; an unrequested model tool cannot execute;
model outage is an error; endless model tool requests stop at the existing round
limit; progress-stream outage emits an error event even though SSE status is 200.

The test transport runs in process without TCP and blocks socket connections.
Application startup workers are not started. This does not prove real OIDC,
notification delivery, service startup, live report custody, connected broker
security or model quality. A fake model response is not an inference request.
The v1 run contract remains synthetic with zero actual model calls. Live-provider
budgets or broader capability profiles need an explicit compatible version.

## Runtime facts and limits

Read-only checks found Aster, broker and approval services active. Live Aster's
source hash matches the baseline. Live broker hash remains the pre-M1 code; the
published correction has not been deployed. Live Aster uses Python 3.13.5 and the
pinned FastAPI/httpx/Pydantic/Uvicorn/PyJWT versions in the manifest. Local tests use
Python 3.12.14, so same-interpreter validation is still required before deployment.

The running inference process resolves to `/opt/llama.cpp-b11081/llama-server`;
its binary, server implementation and Vulkan library hashes match the dated B60
record. A source-local allowlist extracted context 8192, one slot, batch 256,
microbatch 128, four threads, flash attention on and IQ4_XS model path. It did not
print the raw process arguments, environment, keys or configuration. No B60
settings or benchmark jobs were changed or invoked.

A host memory snapshot showed 47,802 MiB available and 1 MiB swap used; inference
cgroup memory was 9,501,990,912 bytes. This is not sustained spare capacity or
permission to allocate it. Model shard hashes remain dated evidence from the
separate B60 project; they were not rehashed for this task.

Machine-readable provenance: [runtime and tests](M2-integration/runtime-and-tests.json).
The existing operational knowledge authorities remain unchanged because there is
no new deployment or inventory fact to publish as a service change.

## M3 preparation and next step

The minimal PydanticAI experiment is now preregistered in
[M3 comparison plan](M3-comparison-plan.md). Official documentation supports a
slim install, `FunctionModel` fixtures and disabling non-test model requests.
A metadata-only dependency resolution for PydanticAI slim 2.51.0 with Pydantic
2.13.4 returned 17 packages. Versions and wheel hashes are retained in
[pydanticai-resolution.json](M2-integration/pydanticai-resolution.json).
No package was installed. The existing test environment has no PydanticAI.

Next: assess this explicit dependency footprint against the no-major-install
constraint and use an isolated, pinned temporary environment only if within the
accepted boundary. Do not alter the Aster environment or install the full bundle.
If that boundary is not acceptable, retain the baseline and record a deferred
challenger; do not fabricate a comparison with handwritten framework-like code.
M3 model-serving measurements need separate resource and compatibility checks.

M1 remains open for independent review, approval trust separation/acceptance,
M6 reconciliation and approved deployment validation. M2 completion does not
waive those gates. Local checkpoint only; no new push authorization was requested.


## Subsequent M3 progress

The 5.45 MB wheel footprint was accepted as a bounded minimal local experiment,
and the challenger was installed only in a new disposable venv. The preload
comparison and its limits are now recorded in [M3 results](M3-preload-results.md).
The earlier no-install/next-step statements above describe the checkpoint before
that later action; no production environment was changed.
