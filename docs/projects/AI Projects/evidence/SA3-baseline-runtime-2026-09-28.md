# SA3 baseline runtime observation

Date: 2026-09-28  
Status: **read-only observation; no inference evaluation or configuration change**

## Observed baseline

The active Aster API and local llama.cpp inference service were confirmed
running through a read-only host inspection. The inference baseline is:

| Property | Observed value |
|---|---|
| Model | Qwen 3.8 27B IQ4_XS GGUF |
| Server | llama.cpp `b11081` |
| Context | 8,192 tokens |
| Concurrent slots | 1 |
| Reasoning | Explicitly off; reasoning budget `0` |
| Aster normal response cap | 160 tokens |
| Service hardening | Dedicated unprivileged service account, private temporary directory, strict system/home protections, and an API-key file not inspected or copied |

The service's private bind address and authentication material are intentionally
omitted. This observation does not establish response quality, latency, tool
use, model configuration suitability, or a provider decision.

## Evaluation implications

The sealed SA3 holdout must run first against this exact non-thinking baseline.
Before the first run, record the request template revision, temperature and
sampling settings actually applied by the Aster client, tool/observation budget,
warm/cold protocol, shared-service load, and timing boundary. The model has one
slot, so the evaluation must run serially and include queue/warm-up conditions
in the timing record.

At most two deliberate local improvements may be compared only after this
baseline result is sealed. Do not enable reasoning, change model settings, or
route to a cloud provider merely to make a result pass.
