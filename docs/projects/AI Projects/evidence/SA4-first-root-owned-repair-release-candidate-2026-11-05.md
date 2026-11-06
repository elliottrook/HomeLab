# SA4 first root-owned repair release candidate — 2026-11-05

## Release candidate

The final no-authority packet now binds the first canary repair to:

- the exact plan `59641703…956`;
- drifted target `19b4e02d…df1a` and candidate `4529dee5…1065`;
- the independently validated installed result `1a4fe005…548ff`;
- the exact live-preflight, final-admission, root-owner and reconciler hashes;
- a fresh measurement and exclusive checkpoint;
- a ready one-use ledger entry claimed once;
- the whole-host lease, shared operation lock and plan-bound emergency stop;
- independent postcheck and rollback observation;
- at most one repair and one rollback, with zero retry and no restart.

The packet explicitly rejects reuse of the expired ceremony grant. It requires
a new exact-plan owner proof and a new exact-plan AI-PAM one-use grant/proof
whose deadlines intersect the transaction window.

## Verification

- installed source pins: 4/4 exact;
- authority/runtime requirements: pass;
- no-effect/no-retry limits: pass;
- release tests: 3/3 pass;
- complete SA4 suite: 146/146 pass;
- whitespace/error check: pass.

The release candidate grants no authority and cannot perform a repair. No key,
signature, grant, ledger, checkpoint, target or service action occurred.

## Immediate gate

The next step would create fresh owner and AI-PAM signed authority for this
exact release and run the single supervised canary transaction. That is the
first real repair effect and requires a new immediate approval. It excludes
all other targets, services, models, networks, credentials and automatic
promotion.
