# M3 NLU token-confidence v7 public gate — 2026-10-26

**Result:** **PASS — six-set nested development is the next gate**

The unchanged accepted Qwen3.5-9B endpoint was first probed with one synthetic
public response. It returned bounded per-token log probabilities, confirming
that an independent confidence signal is available without loading a model,
changing configuration or restarting a service.

Candidate v7 keeps the already-frozen three-perspective v6 semantics and
deterministic unresolved-referent rule. Each request additionally asks the
existing endpoint for token log probabilities. A perspective's confidence is
the geometric mean token probability. Decision confidence multiplies semantic
agreement by mean perspective confidence; route confidence multiplies route
agreement by mean confidence among route votes. Missing, nonfinite, positive or
oversized confidence data fails that perspective closed. The output grants no
authority and automatic routing remains off.

The exact 24-case public development gate produced:

- attempted and valid: **24/24**;
- exact interpretations: **23/24**;
- unsafe false routes: **0**;
- routed privacy underclassifications: **0**;
- result SHA-256:
  `72a27fb44b343d3a5a6fa7511aa1453f082803ff09fc97f5d761f75bef133dcc`.

The complete dependency-free NLU suite passes 356/356. The accepted model and
Aster Agent remained active with zero restarts; the whole-host lease returned
`ready`. All public-gate files were removed from Proxmox and LXC110 after the
result was reconciled.

This pass authorizes nothing by itself. The candidate must next pass nested
leave-one-set-out threshold selection over the six already-spent development
sets. A fresh calibration is prohibited until that succeeds, and the sealed
holdout remains unopened.

