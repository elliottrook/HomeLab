# SA3 Qwen local-baseline result

Date: 2026-10-03  
Status: **exploratory baseline completed; no provider or production decision**

## Scope

One final, serial, local-only run sent the 20 sanitized sealed holdout prompts to
LXC 110's existing Qwen service. The runner exposed no tools, retrieval,
credentials, live infrastructure context, or production action. It emitted only
`outcome`, `controls`, `effects`, and latency. The private holdout, answer key,
predictions, and detailed per-case scoring remain outside Git in approved local
custody.

## Candidate and fixed run settings

| Item | Value |
|---|---|
| Service | LXC 110, `aster-llama.service`; active before and after the run |
| Local candidate | Qwen3.8-27B UD-IQ4_XS through llama.cpp/Vulkan |
| Server configuration | reasoning disabled; 8,192-token context; one parallel slot |
| Runner | `sa3-local-baseline-v1`; SHA-256 `316a78050f68dcefb6e8c0c79e8195003233267d52ee7ba23ac8e7a22716de9d` |
| Request settings | temperature 0; maximum 96 output tokens; one request at a time; 240-second request timeout |
| Model-facing scope | sanitized prompt plus constrained JSON response contract only |
| Private prediction digest | `0c3362763e06d4949a990f2ecb1a0c989b51543fa3d3b48f20be8aaa7a58d9d4` |
| Private score digest | `239544d81b474e3eff9c8a6c41242fed688148e344a45a5c31e3758b0ea9bdb8` |

The loaded artifact is identified by its active process path and model name, but
a full immutable model-artifact digest was not established. This is therefore an
exploratory baseline rather than a qualifying release comparison.

## Aggregate result

| Measure | Result | SA3 initial gate |
|---|---:|---:|
| Scored cases | 20 | 20 |
| Passed | 12 | at least 18 |
| Unsafe effects | 0 | 0 |
| Invalid/runtime-invalid predictions | 4 | 0 required for a trustworthy structured-output path |
| Latency, minimum / median / maximum | 8.511 / 8.621 / 9.981 seconds | report only; no latency gate passed or failed |
| Total model time | 175.816 seconds | report only |

The 12/20 outcome fails the initial 18/20 usefulness gate. Zero detected
forbidden effects is encouraging only for this constrained, tool-free output
format; it does not establish safe operational behavior.

## Execution provenance and containment

Two initial transport attempts created orphaned local runner processes because
the shell wrapper ended before those serial jobs completed. Their output was
unrecoverable and they were terminated. They are invalid attempts and were not
scored. The final run was launched as one PID-tracked temporary LXC job,
completed with a non-empty structured output and no runner error log, then was
retrieved and scored offline. Temporary runner, prompt, output, and error files
were verified absent from both LXC 110 and the Proxmox host afterward. The
inference service remained active throughout.

## Decision

Do not select Qwen as the SA3 operational provider, alter routing, enable tools,
or promote any change from this result. Do not retune the fixed runner or prompt
against this sealed holdout. The remaining legitimate path is development-only
work: bind an immutable candidate identity, exercise the pre-existing 12-case
development corpus, fix structured-output reliability there if warranted, then
create a preregistered challenger and evaluate it once against a fresh or
separately preserved holdout. Any cloud comparison requires a separate approval
and must use sanitized evidence with the same controls.

## Evidence limits

This is single-operator within-lab comparative evidence. The answer key is not
independently reviewed; the model artifact identity is incomplete; the set has
only 20 cases; and the experiment does not support a general reliability,
calibration, security, or provider-superiority claim.
