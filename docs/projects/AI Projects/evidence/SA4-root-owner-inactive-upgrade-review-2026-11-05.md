# SA4 root-owner inactive upgrade review — 2026-11-05

## Fresh installed baseline

Read-only LXC104 verification found:

- preflight composition: `d96fcba0…ea06`, root:root 0644, one regular link;
- receipt/ledger reconciler: `d69ef159…aefc`, root:root 0644, one regular link;
- final effect admission: absent;
- root transaction owner: absent.

## Candidate

The exact inactive upgrade contains four files:

- replace the preflight composition with `a38ccb0b…d11`;
- replace the reconciler with `9688ae6e…69a1`;
- create the final effect admission at `16d6bba0…040b`;
- create the root transaction owner at `d8a6d69a…1c39`.

Both predecessors must be retained root-only under the fixed checkpoint path.
Both new paths must be absent. Rollback restores the exact predecessors and
removes only the two exact newly created files, and stops without guessing on
any mismatch.

## Verification

- exact source pins: pass;
- two replacements plus two exclusive creations: pass;
- inactive exclusions and reverse rollback: pass;
- packet tests: 3/3 pass;
- complete SA4 suite: 140/140 pass;
- whitespace/error check: pass.

This review made no live change. It grants no authority and invokes no key,
signature, ledger, checkpoint, receipt, target operation, service, schedule,
booking, model or route.

## Gate

Installation is a separate explicit effect because it changes four live
LXC104 files. It remains inactive after installation: all effect-capable host
bindings remain unconfigured and the root owner is not invoked. The first real
repair remains a later immediate exact approval gate.
