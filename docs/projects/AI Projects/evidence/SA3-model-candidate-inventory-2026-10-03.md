# SA3 model candidate inventory

Date: 2026-10-03  
Status: **read-only inventory; no evaluation run or model selection**

## Scope and method

This is a narrow, read-only inventory of the live local inference candidate for
SA3. It used a direct authenticated host query to inspect LXC 110's service and
resource state. It did not read credential files, submit a prompt, contact a
cloud provider, change a service, or select a provider.

## Verified current state

| Property | Observed value | Implication for SA3 |
|---|---|---|
| Candidate service | `aster-llama.service`, LXC 110 | A local baseline candidate exists. |
| Service state | active and enabled | It is running infrastructure, not an isolated evaluation fixture. |
| Process | `llama-server` on `192.168.70.12:11435` | Any future run must use the existing authenticated service contract. |
| Model artifact selected by process | Qwen3.8-27B UD-IQ4_XS, first GGUF shard path | This identifies the loaded candidate; it does not establish an immutable model-artifact digest. |
| Configuration | Vulkan, 8,192-token context, one parallel slot, non-thinking mode | The baseline is capacity-constrained and serial; comparison runs need a conservative token budget and shared-load measurement. |
| Container state | running; load averages 0.97/0.90/0.93; 9,154 MiB of 16,384 MiB reported used | A point-in-time observation only. It does not prove sustained capacity or idle availability. |

## Interpretation

The active Qwen service is eligible only as the **current local baseline
candidate**, subject to a separately approved, rate-limited, read-only SA3
evaluation run. Its one-slot configuration means that an evaluation should be
serial, bounded, and scheduled so it does not compete with household or Aster
requests. The inventory does not demonstrate answer quality, calibration,
latency under controlled load, artifact immutability, or comparative advantage.

No secondary local model or cloud provider is selected. The legacy Ollama path
and any external provider remain repository intent or future candidates until a
separately scoped inventory and experiment authorize them.

## Pre-run gates

Before a model is sent any sealed holdout prompt, record all of the following:

1. a stable model-artifact identity or accepted immutable release manifest;
2. exact request template, response limit, temperature and timeout;
3. warm/cold and shared-service load protocol;
4. a fixed prediction-file writer that cannot call tools or production systems;
5. explicit approval for this one read-only model run;
6. post-run scoring with the frozen private answer key and evidence limitations.

The holdout remains prohibited from retrieval, prompt tuning, harness tuning,
provider selection, or production promotion. Results remain single-operator,
within-lab comparison evidence.
