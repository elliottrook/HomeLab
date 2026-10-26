# Stream A pre-F2 continuous-work check — 2026-10-25

Status: **PASS — OFFLINE WORK CONTINUED; TIMED F2 CHAIN UNCHANGED**

## Purpose

Use the period before the October 26 F2 preparation window for useful Stream A
work that does not need an exclusive B60 lease or compete with backups. This
check neither substitutes for F2 runtime evidence nor authorizes a later gate.

## Reconciliation completed

- Canonical architecture, addressing and Aster operations now describe the
  accepted llama.cpp b11429, Qwen3.5-9B Q4_K_M, SYCL/Level Zero production
  runtime rather than the retired Vulkan/27B runtime.
- Active recommender and collection-planning documents now use the same current
  shared-inference identity. Historical experiment evidence remains unchanged.
- The programme and delivery map now expose the current D3, M1, D4, M3 and
  F2–F6 state without requiring the owner to reconstruct it from chronology.
- The platform lane still owes the current-packet F6 activation/recovery card;
  no activation, lease, consumer stop or model request was inferred.

## Offline validation

| Boundary | Result |
|---|---:|
| Complete D4 evaluation suite | 168 / 168 passed |
| Candidate-H launcher and target validator | 13 / 13 passed |
| Dependency-free formal NLU suite | 116 / 116 passed |

The complete NLU discovery command additionally reached the optional
`test_nlu_benchmark.py` dependency boundary because the macOS system Python
does not contain Pydantic. That module was excluded for the declared
dependency-free run; all remaining 116 tests passed. This is expected and does
not change the pinned LXC110 packet, whose target interpreter/dependencies were
already validated separately.

## Live boundary

No model call, credential read, lease, service restart, schedule change, F2
service invocation or remote push occurred. The exact October 26 timers remain
the authoritative timed path: prepare at 01:15 PDT, final/read-only scan at
01:20, and observation-only reconciliation at 01:42. Fresh backup, TrueNAS,
archive-identity, quiet-host and absence gates still decide whether the scan
runs.
