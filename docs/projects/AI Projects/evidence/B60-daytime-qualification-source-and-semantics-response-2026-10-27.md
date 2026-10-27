# B60 daytime qualification source and semantics response — 2026-10-27

## Published source

The final platform source is published on
`codex/f2-observer-exit-diagnostics` at full commit
`200640648eca0d3485eae8e2cbfd2707a0e3c296`. Read-only checks returned that
exact ref from both Forgejo and its GitHub mirror. The platform result file
`services/local-ai-lease/FULL-INFERENCE-DAYTIME-TWO-PASS-QUALIFICATION-RESULT-20261027.md`
has SHA-256 `1ca68589e9576bc8e43402cf38915b3b3b666d99ec4f818fe6ec886fb19fcae3`.

The Stream A record is published on `codex/aster-stream-a-handoff` at
`e900153940c9615e6e5a4af7049263b01dd5d456`. The two-pass evidence at the
earlier published checkpoint retains SHA-256
`631fa9df8cd33a1da63d52abf0beceb125389e6882ae023161bd5090a5426072`.

## Installed two-pass manifest

The two accepted passes used this installed set:

| Installed artifact | SHA-256 |
|---|---|
| `cooperative_lab_host_adapter.py` | `068ea9b85e31116ec13f4f27b8b1207d46e3569aa35c95440c644cce969f515f` |
| `full_inference_lab_deadline_guardian.py` | `b7cbc3992868400b95e90cd783b26511e1c4f2a2f2b587b6f111c0a58dd4b96f` |
| `full_inference_lab_runtime.py` | `c4f131baec043511e525bb3babfa9a0b11236d4de1f399b2152c43f288cc79b9` |
| `full_inference_lab_session.py` | `02fe37d6ee0d6a88133b2998dcf1badeaa086fb6f0f36114a3c2fe3321857b40` |
| `full_inference_lab_sources.py` | `91daf38fa757f301524fb929ab2581abb0895d776d144fbb9da995ca09435266` |
| `full_inference_lab_supervisor.py` | `da5ac76fb48541a2661caa1cb4fe7f21d84334abb9ab935fb1aaaf72c4faba55` |
| `full_inference_lab_validator.py` | `18a09b74f276a4fa5cadd7270efa9922f14a026e77e00debe7a8b7ade8ed56a1` |
| `full_inference_lab_workload.py` | `b0ad8a6422d4290cd73568916de4e35ef05130e5b93aee22c629ce7560beb236` |
| LXC110 `aster-llama-lab-smoke` | `fec8b0a07a3d13a35a04eea80e460e4422de288ef69f9a2b18a00f3ebb228870` |

## Measured model and timing boundary

Both passes used the accepted production candidate: Qwen3.5-9B Q4_K_M,
llama.cpp `b11429`, SYCL/Level Zero and alias `aster-qwen3.5-9b`. The final
production model, binary and unit hashes were respectively
`cd76ec20…2a13`, `0404f751…e6c5` and `a4c75169…4cb3`.

This is not a 35B result. It does not establish a 35B mount, cold-load,
switch or restoration reserve.

Each accepted complete transaction took 109 seconds wall-clock:

| Pass | Start | Complete | Total |
|---|---|---|---|
| 1 | 08:47:31 PDT | 08:49:20 PDT | 109 s |
| 2 | 08:50:39 PDT | 08:52:28 PDT | 109 s |

The retained pass envelopes contain only declared start, finish, exit status
and bounded controller result. The append-only transaction journal preserves
ordered drain, heartbeat, restore and verification events but has no per-event
timestamps. Therefore no sanitized per-stage duration can be reconstructed
honestly from these passes. A new challenger card must instrument monotonic
timestamps for drain, model mount/load/readiness, workload, production
restoration and final verification before using those timings for the
30-minute B60 or 04:15 completion bounds.

## Enforcing F4 semantics

The enforcing Stream A rule is the October 26 same-cycle correction:

- F2, F3 and F4 bind the same local date and unchanged archive rows;
- F4 is written only after that date's fixed 03:00 pull, with a fresh
  production observation and separately fixed lease identity;
- F4 remains a distinct effect decision and does not inherit authority from
  F3; and
- F6 must arm independent owner/watchdog recovery before any consumer effect.

The October 28 F3 review/card sentence saying F4 requires a “subsequent fresh
cycle” is stale wording inherited from the earlier card. It must not control a
challenger admission because it would make the retained F3 receipt unusable
after midnight. The installed evidence loader and retained-integrity verifier
enforce same-local-date, unchanged-row binding.

## Consumer and resume ownership

The two-pass transaction isolated the accepted llama.cpp service, Aster Agent,
Speech and the two fixed News timers. The later network audit additionally
identified News ingestion, Paperless summaries and EPUB narration as scheduled
inference callers or material fixed-guest workloads. The October 28 F2-only
exclusion blocks those three from 00:15 until its unconditional 03:50 resume.

That exact-date resume is safe for the current F2/F3-only sequence, which ends
well before 03:50. It is not suitable for a later challenger lease that may
remain active from 03:10 through 03:55 or toward the 04:15 completion bound.
Such a card must include all actual consumers in the admission snapshot and
make resume lease-aware: the active lease/recovery owner must retain authority
until exact production restoration completes, and no independent timer may
re-enable a caller while the lease or recovery state exists. The card must
also retain no-retry behavior and the 30-minute B60 and 04:15 outer bounds.

This response supplies source and semantics only. It approves no challenger,
lease, service stop, model call, schedule change or operational run.
