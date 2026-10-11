# Stream A impact of the 9B local-model promotion — 2026-10-10

## Decision

**Do not roll back to 27B on the evidence available.** Keep 9B under observation for its bounded local-answer role, with the retained 27B unit as a recovery option. This is not a promotion of local AI to general sysadmin, nor a D3/M1/automatic-routing gate pass. Reverse the model change if a consequential answer regression, failure of an existing consumer, or sustained reliability/capacity regression is demonstrated. A model rollback is an operational change and needs its own preflight and authority check.

## Provenance and observed state

The attachment `2026-10-10-aster-model-change-synopsis.md` supplied by Jason reports a frozen 20-case synthetic suite (16 model-handled), human semantic review 16/16 for both 9B reasoning-off and 27B reasoning-off, and controlled median latency 2.488 s versus 11.051 s. It reports mechanical scores 12/16 versus 15/16; the author attributes the 9B misses to exact-word/presentation mismatch. The underlying per-case reports and independent review were **not available in this checkout**, so this is report evidence, not independently reproduced benchmark evidence. Small synthetic coverage does not establish long-tail or real-user equivalence.

Independent read-only checks via Proxmox confirmed LXC 110 `aster-llama.service` is active/running with zero restarts. Its active unit selects `/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf`, has reasoning off and one 8K slot, and matches the synopsis unit SHA-256 `6b09f458...`. The retained `aster-llama.service.pre-9b-20261010` matches the synopsis rollback-unit SHA-256 `e2019cac...`. LXC 104 `aster-agent.service` is active with zero restarts, and its source SHA-256 matches the synopsis `a311a020...`. No generation, model load, restart, deployment, or credential read was performed for this review.

## Reconciliation items before treating this as a stable Stream A baseline

1. The synopsis names local commit `ce84b28`, but it is absent from this repository object database and the current Stream A worktree. The main checkout also has unrelated uncommitted work. Do not overwrite or merge either checkout blindly. Obtain the exact implementation/evaluation commit and reconcile it with this branch before changing model-dependent code or publishing documentation.
2. The deployed Aster `/etc/aster/aster.env` still sets the non-secret selector `ASTER_LLAMA_MODEL=qwen3.8-27b`. `build_payload()` sends that selector upstream even though the inference unit loads 9B and `/v1/models` advertises `aster-qwen3.5-9b`. Backend alias tolerance and any consumer impact are **unknown** without a bounded functional check. Align the selector with the loaded model under a separately reviewed change; avoid changing it during Jason's B60 experiments.
3. The synopsis's `summary/facts/uncertainties` contract describes the model-selection evaluation. The deployed general chat endpoint still accepts a broad chat request, persona selection and preloaded context; it does not visibly enforce a three-field response schema. Existing deterministic tool permissions and broker checks remain a separate boundary, but do not claim the *whole production assistant* is limited to those three outputs. Verify the intended boundary before using this model result to expand scope.
4. Model-specific strings and 27B defaults remain in the Stream A repository's Aster source, service unit, warmup, tests, runners and operational reference. These are reconciliation work, not grounds alone for production rollback. Historical 27B benchmark records should remain historical.

## Stream A consequences

D3 manual subscription-backed Codex handoff and M1 AI-PAM authority work can continue offline; both are model-independent. Do not repeat the closed general-sysadmin local-Qwen trial or infer that a smaller model can do Codex's deep sysadmin work. A future Decision Plane should register 9B as a bounded local capability, with measured task-specific quality and availability, and preserve deterministic routing/authorization plus escalation. The read-only routing corpus must identify the exact model/runtime, so pre-change and post-change results are not pooled silently. During Jason's concurrent B60 experiments, defer live generation and capacity tests.

Reassess after the cited commit and per-case reports are available, the selector/metadata are reconciled, and a short observation of real bounded tasks and dependent services is complete. Roll back only on a defined failure signal or if the reconciliation exposes a material control bypass; do not roll back merely because 27B is larger.
