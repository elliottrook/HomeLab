# B60 inference benchmark harness

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
