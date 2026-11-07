# M3 K3 runtime manifest and platform handoff — 2026-11-06

## Result

The exact K3 source-only runtime manifest was frozen at Stream A commit
`8e0a60d9` and received its engine-result lineage correction at `dd6cd011`. It
binds workload
`m3-k3-hierarchical-safety-development-v1` to candidate
`k3-hierarchical-safety-veto-v1`, LXC110, the accepted 9B/SYCL model and unit,
the fixed J2 corpus/shortlist/preregistration identities, both permitted
production and booked-loopback endpoints, and twelve exact source files.

The validator passes 3/3 focused tests and the complete K-series suite passes
145/145. Endpoint, source, model, runtime-effect, sealed-access and authority
drift fail closed.

## Frozen identities

- manifest validator SHA-256:
  `851034f96837e8863882d6a67dfffddbe7f386500d1dca5092f4c68a9c49b964`;
- manifest test SHA-256:
  `57a2b8b911e007d717747df7971f0431f0d3954f04ae08563dc2f1a8f2849cc5`;
- runtime manifest SHA-256:
  `0a9866a10c4079879fc7d7e8298969074cc50e44b36afd3b1c56e570fe08fa45`;
- runner SHA-256:
  `940d1de888bc00709f37db09604bd7062dbd9553dbdc970e7d9c8d705378bf96`;
- runner source commit: `dd6cd011`;
- scorer source commit: `b81ba688`; and
- hierarchical safety/preregistration source commit: `662b52e5`.

## Runtime envelope

- cases / model requests: 192 / 384;
- attempts / retries: 1 / 0;
- wall deadline / per-request timeout: 1,800 / 45 seconds;
- minimum booking / recovery reserve: 3,600 / 900 seconds;
- own registered workload and authoritative Lab Hours booking required;
- whole-host lease and shared operation lock required;
- booked full-drain restoration required;
- tools forbidden, sealed evaluation inaccessible, authority not granted and
  automatic routing off.

The predecessor K2 root-custodied run provides a direct capacity check: its 192
model requests took 185.531 seconds and its complete drain-to-restoration
transaction took 427 seconds. K3 doubles the calls but retains a 1,800-second
workload deadline and a 900-second recovery reserve. This is evidence that the
envelope has substantial measured margin, not permission to skip live admission
or restoration gates.

## Platform handoff contract

The platform owner must create a distinct, deterministic K3 registration and
runner path rather than edit or replay K2. The inactive packet must:

1. install the twelve exact runtime sources plus unchanged corpus and shortlist
   custody in LXC110;
2. register only `m3-k3-hierarchical-safety-development-v1` with 384 requests,
   zero retries, 1,800-second deadline and 900-second recovery reserve;
3. route the fixed runner kind through the existing full-drain owner, private
   loopback listener, root-custodied result, guardian and accepted-production
   restoration path;
4. validate the content-free K3 score and retain both terminal and first
   failure without opening sealed evaluation data;
5. prove exact release-manifest, registry, guest custody, dependency closure,
   output absence, dispatcher, lease, lock, model and schedule gates;
6. support reversible inactive installation with a rollback checkpoint and no
   model call, service restart or booking during installation; and
7. after final activation and booking, receive an independent read-only
   readiness verdict for the new runner kind before effects.

Only after registration and inactive validation may the complete proposed
execution plus recovery window be checked with the authoritative ledger. A
booking may name only this registered workload. A scheduled record alone is
not readiness; the dispatcher-to-guardian path and live production postchecks
must pass immediately before effects.

## Boundary and exact next action

No platform mutation, workload registration, booking, lease, service action,
model request, route, tool or promotion occurred. The source branch must be
made available to the platform owner through the named Forgejo branch, then the
platform owner can build and return the inactive registration/install packet.
The Forgejo push is the next external action and requires its immediate remote-
write confirmation under `AGENTS.md`.
