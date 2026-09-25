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
