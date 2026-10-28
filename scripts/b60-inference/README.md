# B60 inference benchmark harness

## Current safety status — 2026-10-26

This is retained offline development tooling, not the current shared lab
controller or an approved execution recipe. Do not execute its legacy guard,
finalizer or endpoint switches against production. The old 00:20 preflight,
01:40 experiment limit, 02:00 restoration deadline and Vulkan recovery checks
below describe historical code, not the accepted SYCL/shared-lease contract.
The old hard-coded nightly coordinator must remain undeployed.

Current admission requires the owning platform's source-bound backup chain,
independent recovery and single runner, with restoration completed before
04:15 America/Vancouver and each B60 trial bounded to 30 minutes. An admitted
D4/M3 9B workload does not admit a B60 model/runtime replacement or full-Aster
answer baseline. The exact challenger and full-path contract remain open;
see the current project coordination status and its pinned owner receipts.
Offline tests and explicit command-line interlocks never grant live authority.

`phase_timing_proposal.py` validates caller-supplied, content-free phase rows
for offline review only. It neither samples clocks nor writes a durable journal.
Its proposal schema is not an accepted platform adapter: source custody,
monotonic collection and journal-sequence wiring still need owner review.
Incomplete/failed phases never become recovery or model qualification proof.

This directory contains the offline, synthetic-only Phase 1 harness. It does
not connect to the inference endpoint, execute SSH, spawn processes or authorize
a production run. A separately reviewed runner can consume the generated plan
only after the Stream M production-load approval gate is satisfied.

Local checks:

```console
python3 scripts/b60-inference/harness.py validate-fixtures
python3 scripts/b60-inference/harness.py plan > /tmp/b60-plan.json
python3 -m unittest scripts/b60-inference/test_harness.py
python3 scripts/b60-inference/harness.py validate-ledger RECORD.json
python3 scripts/b60-inference/harness.py summarize RECORD.json
python3 scripts/b60-inference/runner.py --fixture pp512-cold-pos0 \
  --endpoint http://127.0.0.1:11435
```

The plan expands deterministic, non-secret prompts and records their SHA-256
values without storing expanded multi-kilobyte prompts in Git. It covers pp512
at 0/4K/8K, pp4096 at 0/4K (8K is outside the accepted 8,192-token slot), tg128
at 0/4K/8K, cold/warm cache states, and the
conversation, persona, read-only tool, grounded retrieval, 2K and 8K Aster
workflow classes. Each case requires one warm-up and five measured repetitions;
the future runner must surround the group with pre/post accepted controls.

Token targets are fixture construction targets, not claims about a particular
model tokenizer. A production runner must record the actual prompt/completion
token counts reported by the pinned runtime and must reject unsupported context
rather than silently shortening it.

`runner.py` is dry-run by default and refuses non-loopback execution unless
both `--execute` and `--allow-production-endpoint` are supplied. Those switches
are safety interlocks, not Stream M approval. The runner brackets each case
with health checks and performs one warm-up plus five measured repetitions.
Execution also requires a new `--output` path; the result is created mode 0600,
fsynced, hashed and never overwritten. Tests use an injected fake transport and
never contact production.

`collect-telemetry.sh` is a read-only, secret-free collector intended to run
inside LXC 110 after separate approval of a benchmark. `telemetry.py` accepts
only its strict key set, rejects duplicate/unknown/credential-like fields, and
converts supported counters to ledger units. Frequency, power and CPU fallback
remain explicit `null` values when they cannot be proven; resident VRAM alone is
not misrepresented as proof that every operation used the GPU.

`collect-kernel-log.sh` runs read-only on Proxmox for an exact epoch range and
caps its output at 500 relevant lines. `kernel_log.py` rejects irrelevant,
oversized, control-character or credential-like content and classifies reset,
device-loss, hang and OOM evidence. CPU fallback is reported true or false only
from affirmative backend/offload evidence plus material resident VRAM;
otherwise it remains unknown.

`record.py` binds the raw runner artifact to its deterministic fixture, exact
environment hashes, telemetry, bounded kernel excerpt, health and backend
evidence. It calculates measured-only median/MAD, refuses incomplete sample
sets, validates the complete ledger schema and writes the resulting record with
the same create-once mode-0600 evidence semantics.

Historical implementation only: `guard.py` accepts a five-minute-fresh preflight collected from 00:20–00:29
America/Vancouver. It requires fresh successful local backup and TrueNAS mirror,
accepted hashes, healthy xe/Vulkan service and fixed disk/RAM/VRAM headroom. No
experiment may start before 00:30 or continue past 01:40; 20 minutes are reserved
for finalization before the absolute 02:00 restoration deadline. The finalizer
stops only the named candidate unit, restarts the accepted service, and validates
its binary/unit hashes, xe binding, B60 Vulkan enumeration and health. It is
dry-run-only unless both production interlocks are explicitly supplied.
