# SA4 distinct-canary v3 release candidate — 2026-11-06

## Result

The fresh-path release candidate is complete and remains effect-gated. Its
canonical packet is `0ca1507a…84cb` and binds:

- plan `e708b2f7…647b` for only
  `/var/lib/aster/sa4/canary-adapter-v2.json`;
- exact drifted-to-healthy digests `a9831e62…4da0` to
  `fae178a1…a0c2`;
- installed v5 owner `a4fd7073…167a` and v6 runner `a91d6a34…a397`;
- the exact inert v6 installation result `6ea88d23…ccbc`;
- fresh input/evidence/ledger paths ending in `v3` and operation identity
  `sa4-canary-v2-second-operation-v1`;
- new grant identity `sa4-canary-v2-second-grant-v1-20261106`.

The failed first grant, owner approval and signatures are explicitly
non-reusable. Its v2 input and evidence paths remain retained and disjoint.
The new authority source is unsigned; it confers no effect and creates no
runtime state.

The complete SA4 suite passes 297/297. No signer, runner attempt, checkpoint,
repair, service action, model change, route or promotion occurred while
building the release. A future live attempt requires fresh owner and AI-PAM
signatures, exact installed/runtime preflight and its own immediately scoped
remote-effect confirmation.
