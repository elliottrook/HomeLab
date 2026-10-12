# Stream A — next lab-card preflight, 2026-10-12

**Scope:** offline planning only. No B60/Proxmox probe, model call, Companion
question, credential access, lease acquisition or production change occurred.
This pass reads the current [Stream A cadence](../Stream-A-Work-Cadence.md),
[development routing benchmark](../benchmarks/ask-routing-development-v1/README.md),
[completed-answer draft](../benchmarks/completed-answer-qualification-protocol-v0.md)
and the separate platform owner's `Local-AI-Platform-Split.md` and
`Environment-and-Release-Lifecycle.md` read-only on 2026-10-12. The latter
files remain owned by that project and were not edited here.

The platform split accepts a single-GPU, whole-host maintenance lease design
but marks the backup moves, controller and after-backup-to-04:15 window as
**proposed, not deployed**. Its V1 accepted inference baseline is
Qwen3.5 9B / llama.cpp b11429 / SYCL on LXC 110. The newer B60 iterative
programme documents named in the coordination request are not present in the
checked-out files available to Stream A. Do not infer their content, active
lease status or a new B60 production release from that request.

## Batched candidate queue

| Card | Question and bounded method | Offline preflight | State / next step |
|---|---|---|---|
| **R1 — next local route profile** | On the already published 30 synthetic requests, does an exactly pinned new local stack improve *status plus capability* agreement without new invalid outputs? No tools, no personal context, one attempt/case, content-free result, existing independent scorer. | Fixture/scorer/manifest contract and 9B 18/30 plus lexical 30/30 controls are pinned. This is a **regression check only**; the lexical rules were authored with the fixture. New candidate model, runtime, reasoning setting, adapter and prompt hashes are absent. | **BLOCKED** until B60 supplies an accepted candidate manifest and the platform owner proves a live lease. Do not rerun accepted 9B just to fill time or tune against exposed cases. |
| **A1 — completed-answer feasibility** | Can the Aster adapter capture complete answers, terminal failures, timing segments and source citations for a small synthetic task slice without leaking raw context into the result? No live tools or personal data. | The [synthetic fixture and offline capture/review candidate](A1-offline-answer-capture-candidate-2026-10-12.md) now cover structural projection and a human-label scoring path. No model output, independent labels, backend-bound provenance or current-control latency exists. | **BLOCKED** for lab use. Build an offline synthetic runner/postcheck and preregister current-control measurement before any finalist comparison. Do not state per-class quality or p95 limits from the routing run. |
| **Q1 — fresh route qualification** | Would a challenger route realistic owner-style requests better than the incumbent under privacy, ambiguity and locality constraints? Tool-free shadow comparison with independent labels. | The old S1 set closed incomplete: 45/50 accepted, no adverse cases. Published 30-case suite has exposed answers. No qualifying hidden corpus or retention decision exists. | **BLOCKED**. A new named protocol, owner-approved custody/retention, independent labels and frozen per-class error floors are needed before collection; this cannot be repaired by relabelling S1. |
| **C1 — Codex Decision comparison** | Can Aster's subscription-compatible Codex handoff return the same content-free Decision fields on the same synthetic requests, with reviewed cloud consent? No tools or infrastructure role. | Existing D3 questions differ and produce no equivalent Decision records. Offline scorer accepts a label-blind adapter shape. | **BLOCKED** until the exact batch, consent, call cap and adapter are approved/tested. This is not a B60 lease task. No new Codex question should be sent to satisfy this card. |
| **D4 — bounded named diagnostic** | Does fresh source-owned evidence identify a fault more usefully than today's aggregate Doctor status, without broader model context or tool authority? | Aggregate `fail` across 32 checks lacks failing-check identity; typed fixture and reader guards exist but have not shown a blinded usefulness gain. M1 Stage2 trust boundary and connected-worker grant remain open. | **BLOCKED** for a connected run. Continue offline source projection and blinded rubric work; no generic shell, SSH or fix follows. |

**Continuous-lane A1 progress:** a six-case, explicitly synthetic/public
[development fixture](../../../../scripts/aster-adaptive/fixtures/answer-feasibility-v0.json)
now covers grounded fact, synthetic calendar, mixed public/private join, fresh
and stale HomeLab reports, and ambiguous household control. Its SHA-256 is
`b5e7748d5c90a30992cb22dd98aa333b3c7c14ea093a16ea3c29069df5661ef0`.
A structural validator checks IDs, source timestamps, bounded fields and the
no-tool scope; 20 focused benchmark/fixture tests passed at the initial
checkpoint. A later [offline candidate](A1-offline-answer-capture-candidate-2026-10-12.md)
adds content-free attempt projection and explicit human-review scoring with 13
focused tests passing. This is *not* an answer-quality run, a privacy
certification or a qualification holdout. A1 remains **BLOCKED** for lab use
until independent review, backend-bound capture, an accepted candidate and a
verified lease exist.

## Shared live preflight for any later exclusive card

Only a separately committed **READY** card may enter a verified lease. Recheck
the controlling platform record and live backup-chain completion, lease owner
and whole-host lock, competing consumers, exact accepted production artifact,
candidate pin, service health, available disk/RAM/VRAM, runner timeout and
evidence custody immediately before its first call. Set a latest safe stop
that leaves a tested restoration and postcheck before 04:15 local time. If any
fact is missing, change the card to **BLOCKED** with no call. Execute ready
cards serially, rechecking volatile facts between them; stop on the first
unexpected failure and preserve partial evidence. A clock reading or a
healthy `/health` response alone proves neither lease ownership nor capacity.

The continuous lane can advance A1's synthetic fixture/schema and D4's
source-projection review without touching the host. R1 waits for a B60
candidate; Q1 waits for human governance; C1 waits for reviewed cloud-batch
authority. None of these cards changes automatic routing, AI-PAM grants, the
D3 limited-release hold or B60's production control.

**Later 2026-10-12 A1 update:** Jason authorized B60 tests now; after the
platform owner's separate light lease was released and production restored,
the [bounded six-case development probe](../experiments/a1-9b-synthetic-answer/RESULT-2026-10-12.md)
ran against the accepted 9B service. Capture and postchecks passed, but the
calendar answer was plainly wrong. This closes only the A1 *capture
feasibility* question. Independent answer-quality labels, current-control
latency distributions, class floors, candidate comparisons and any routing
promotion remain blocked.
