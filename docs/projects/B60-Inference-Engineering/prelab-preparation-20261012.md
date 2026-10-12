# Pre-lab preparation and measurement questions

Date: 2026-10-12. Status: offline preparation complete for this checkpoint;
joint completed-answer contract, shared lease and safe guest staging pending.
This does not authorize a live run or assert any candidate improvement.

## Coordination receipt

Fetched both named project branches; Adaptive remains at `0b5fbdeb`, B60 return
at `5bd0dc78`. No later receipt or completed-answer contract was published at
this check. Adaptive coordination interface `828c6834` and routing scorer are
received; no need to ask Jason to relay that agreement again.

Implemented `routing_review.py` against the real Adaptive scorer, pinned at
`d8d5641dde28bf8e3b94ed180ef4e994d516a7644d459d6adb6c0cd3b7f41f6a`.
It reproduces 30 valid / 18 exact and preserves per-family results. Its output
explicitly cannot qualify answer capability or authorize production deployment.
Calendar, mixed and private-context route families are 0/3 each; these are
development diagnostic gaps, not statistical population estimates.

## Proposed measurement interface for Adaptive review

Adaptive owns task labels, capability policy, required evidence/outcomes,
hard safety failures, case splits and scorer. B60 supplies versioned stack
identity and measured latency/resource records. The provisional local summary
gate is not your schema; implement an adapter only after your format is frozen.

Please resolve/publish these specific fields in the joint contract:

1. Which **completed-answer task classes** are first in scope and which are
   deterministic paths measured without LLM calls? Keep route and answer scores
   separate; do not reuse route p50 0.634/p95 0.705 as answer budgets.
2. For each class: observable completion/correctness, supported abstention,
   mandatory privacy/tool failures, evidence freshness and capability quality
   floor. Which differences count as meaningful improvement, not formatting?
3. Exact latency start/end events: propose accepted Aster request entry to final
   complete validated useful result, including retrieval, reasoning, model/tool
   calls, retries and errors. Report first useful content separately; neither
   acknowledgment nor thought tokens stop the clock. Separate STT/TTS timing.
4. Freeze original 9B comparison anchor, cache/context/load profiles and task
   population. Use paired case IDs; preserve outcome completeness across models
   rather than forcing equal tokens on semantic tasks. Fixed-128-token engine
   diagnostics remain separate. Keep timeouts/failures visible, never drop slow
   cases from percentile reporting or replace them with successful reruns.
5. Development versus independent qualification custody: case IDs/opaque hashes
   can be exported, held-out answer labels remain with Adaptive. No tuning against
   the qualification key. At least 100 latency observations per accepted class
   is an engineering starting point, not a rare-safety or statistical guarantee;
   specify sufficient case diversity, sessions and uncertainty method.
6. Bounded run plan: derive each chunk from expected request costs and remaining
   shared lease, with independent recovery margin. A complete multi-class
   qualification may span several nights. Do not squeeze all p95 evidence into
   one 30-minute run or claim two sessions alone establishes statistical safety.
7. Exact route/role promotion gate, GPT fallback and shadow/canary requirements.
   Better local quality does not grant tools or authorize personal-cloud egress.

B60 can construct telemetry/metadata adapters and run shape/drift/failure tests
now. It cannot invent numerical quality floors or completed-answer budgets.

## Read-only resource snapshot — not nighttime preflight

Observed 2026-10-12 15:39:33 America/Vancouver (22:39:33 UTC):

| Resource | Exact observed value |
|---|---:|
| Proxmox root available | 59,440,783,360 bytes |
| Backup volume available | 2,828,606,103,552 bytes; not a default model staging target |
| Host MemAvailable | 45,188,861,952 bytes |
| LXC110 root available | 22,339,231,744 bytes |
| LXC110 assigned RAM | 16,384 MiB |
| LXC110 swap limit | 512 MiB |
| LXC110 reported MemAvailable | 4,269,301 KiB on subsequent check |
| Accepted service | active, NRestarts=0 |
| Candidate service | inactive |
| Proxmox all-guest backup | still enabled at 02:30 |

The guest's `/dev/shm` filesystem advertised 36,613,238,784 available bytes,
but that is NOT the guest's 16 GiB cgroup memory allowance. Do not infer tmpfs
fit from filesystem capacity. These observations are preparation only and do
not replace fresh archive/mirror/device/resource/kernel gates in the lab lease.

## Revision-pinned candidate acquisition plans — no weights downloaded

Public Hugging Face API metadata supplies exact bytes and SHA-256 below. Both
conversions are published by ggml-org (runtime maintainer), not official model
publisher quantizations; conversion provenance/architecture and retained model
license must still be verified before load. No custom model code is run.

| Candidate | Source-model revision/license | GGUF repository revision | File / exact bytes |
|---|---|---|---|
| Qwen3.6-35B-A3B | `995ad96eacd98c81ed38be0c5b274b04031597b0`, Apache-2.0 metadata | `ggml-org/Qwen3.6-35B-A3B-GGUF` / `baec3ebee244827cda0f4557eafa8b28f7545fa6` | `Qwen3.6-35B-A3B-Q4_K_M.gguf` / 20,419,565,568 |
| GLM-4.7-Flash | `7dd20894a642a0aa287e9827cb1a1f7f91386b67`, MIT metadata | `ggml-org/GLM-4.7-Flash-GGUF` / `7559e96b7e324ab405897dc2b91492b0f376ad4a` | `GLM-4.7-Flash-Q4_K.gguf` / 18,244,193,920 |

Qwen GGUF SHA-256:
`671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`.
GLM GGUF SHA-256:
`b6019edc5fbe37d3660d2e994d16c839a7855a6f03362c5dcf8142ba479cd0d2`.

Neither file fits guest root while retaining the existing 20 GiB free-space
gate, even without runtime workspace. Neither fits a full-file tmpfs within
16 GiB assigned RAM. Host disk can accommodate one artifact while retaining
20 GiB headroom, but the guest still needs a reviewed **transient read-only
host-backed staging path** and exact teardown/recovery. Do not change LXC mount
configuration or reservations during normal production to solve this silently.
No storage expansion or accepted/rollback artifact deletion is proposed.

Full official Qwen source weights are 71,903,776,776 bytes before conversion
workspace, exceeding the observed host free space. Reject that conversion path
for this snapshot. A guessed Qwen-owned GGUF repository returned 401; no token
was supplied and no new access was enrolled. Use the verified maintainer artifact.
Actual GGUF/GPU residency, KV cache, workspace peak, thinking template and
installed b11429 architecture compatibility remain unproven. Do not infer that
an artifact smaller than 24 GB automatically fits a safe 24 GB serving envelope.

Sources: [Qwen source](https://huggingface.co/Qwen/Qwen3.6-35B-A3B),
[Qwen GGUF](https://huggingface.co/ggml-org/Qwen3.6-35B-A3B-GGUF),
[GLM source](https://huggingface.co/zai-org/GLM-4.7-Flash),
[GLM GGUF](https://huggingface.co/ggml-org/GLM-4.7-Flash-GGUF).

## Tests, limits and next safe actions

`candidate_preparation.py` computes byte/headroom fit without downloading,
mounting or granting runtime authority. Seven synthetic tests cover missing
pins, traversal/duplicate artifacts, invalid bytes and cgroup-vs-disk fit.
Six routing-adapter tests cover published baseline reproduction, scorer/fixture/
run drift, enabled tools and false qualification labels. All 67 B60 harness
tests and eight Adaptive routing-scorer tests pass (75 total).

Next: agree on the actual completed-answer export, extend the adapter and
timeout/failure accounting offline, review the transient staging path with the
shared lease owner, then stage only the first compatible candidate after fresh
capacity checks. Normal production/schedules/TTS are unchanged. No live GPU
load, download, guest mount, driver change, disk growth or Git push occurred
for this preparation checkpoint. Publication of a follow-up requires its own
immediate push approval; local readiness is not agent receipt.
