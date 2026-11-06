# SA4 distinct-canary v2 release-candidate review — 2026-11-06

**Decision: release candidate complete; exact live repair approval is the next gate.**

The retained no-authority release digest is
`364c5c4d779339ba5682bfac57ef17632614360889bf6263446e1145e2b0300e`.
It binds the validated inactive-install result `ce44e3ab…1a02`, all three
installed v4 sources, four release sources and exact plan
`e708b2f7…647b`.

The plan permits only the registered LXC104 v2 canary path to move from the
measured drifted digest `a9831e62…4da0` to the fixed healthy digest
`fae178a1…a0c2`. It requires an exclusive checkpoint, one-use grant, fresh
whole-host lease and operation lock, independent observer proof and production
postchecks. It forbids automatic retry, service restart, routing and promotion.

Fresh unsigned owner and AI-PAM inputs were built for only this plan. Grant ID
`sa4-canary-v2-first-grant-v1-20261106` is new, single-use and shorter-lived
than the owner approval. The detached statements contain no signature and
confer no effect. Prior approvals and grants are explicitly non-reusable.

The complete SA4 suite passes 277/277. No signer, input directory, ledger,
checkpoint, repair, service action or model path was invoked. A live run must
still receive one exact effect approval and recheck every fresh runtime gate.

