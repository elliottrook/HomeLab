# SA3 development structured-output result

Status: **development-only conformance evidence; no holdout retest or promotion**

The exposed 12-case SA3 development corpus was run once through the local Qwen
candidate with llama.cpp's schema-constrained JSON response format. This was an
intentional development challenger after the exploratory holdout baseline
recorded four malformed outputs.

| Measure | Result |
|---|---:|
| Development cases | 12 |
| Valid permitted outcome token | 12/12 |
| All three required controls present | 12/12 |
| Empty effects array | 12/12 |
| Invalid structured outputs | 0/12 |
| Median model latency | 9.065 seconds |
| Private prediction digest | `9acafe5de9eed20acdb94092115840a7fd821a264334683fd9ff6ef1aa8edfed` |

The final run was PID-tracked, local-only, serial, tool-free, and error-free.
Its temporary runner, input, output, and error files were removed from both LXC
110 and the Proxmox host after retrieval. The model service remained active.

This establishes only that the exact current server accepted and conformed to
the output schema for the exposed development cases. It does not establish
investigation quality, incident-plan correctness, calibration, safety beyond the
format, provider selection, or improvement on the sealed holdout. The holdout
must remain untouched while a preregistered evaluation plan decides whether a
fresh independent comparison is justified.

The llama.cpp server documentation describes `response_format` support for
schema-constrained JSON, but its compatibility varies by build; this local
result is the relevant evidence for this environment.
