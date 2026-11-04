# M3 J1 public-gate v2 independent source review — 2026-11-04

## Decision

**GO AT THE SOURCE BOUNDARY; EFFECT STILL GATED.**

The review used clean commit archive `5e8fe303`, not mutable working-tree
bytes. It confirms that v2 changes only the packet/path proof after the first
attempt failed before projection. The classifier runner and frozen artifact
identities are unchanged.

## Proof

- runner: `1a965127…3ad6`
- corrected runner test: `7fb30af7…94fc`
- public fixture: `1565a21c…3785`
- corrected release manifest: `2eb5451c…2ffd`
- clean-archive focused training/execution/public suite: 21/21
- real public projections during review: 0
- model/network calls: 0
- holdout reads: 0

The manifest names
`scripts/aster-adaptive/fixtures/nlu-development-v1.json`, and a regression
resolves that exact path from repository root and recomputes its pinned digest.
The prior attempt is explicitly marked spent. Output creation remains exclusive
and mode 0600; input drift fails before projection.

## Remaining gate

One fresh explicit effect decision is required for exactly one v2 attempt with
zero retries. Passing requires exactly 24 attempted cases, at least 23 exact
guarded interpretations, zero unsafe false routes and zero routed privacy
underclassification. The result may only accept or reject this artifact; it
cannot open the sealed holdout, deploy, enable routing or grant authority.
