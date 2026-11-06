# SA4 distinct-canary v3 transaction source boundary — 2026-11-06

## Result

The distinct inert v2 canary now has a source-complete fixed transaction path.
It cannot resolve or reuse the spent original canary, and it uses separate
create-only input, evidence and one-use-ledger paths.

The complete SA4 suite passes **249/249**. This is source evidence only. No
file was installed, no authority was created, no signer or runner was invoked,
and no repair, service action, restart, route or promotion occurred.

## Frozen source identities

- accepted v2 registry:
  `86c442725544480c85c6bdb5507c17d48acc16e58994e32fffaae944f696da39`;
- v3 root transaction owner:
  `2b2d08249072c52dd5e2f79ff3f525bdb46c647a79225993e964dd6e7dd49fb0`;
- v3 fixed no-argument runner:
  `9c6bfbbe05dfa6d574988df3a99b79696fcfee1353d24461324806df2ec0cc9f`;
- canonical release packet:
  `47c68ba428e30dc32e154f46f889f0231d9e6c2d1c56801d9589d7510ca76c93`;
- accepted inactive seed-install result:
  `299553312a2c247a87aec8a70925cf08a45553da101e5d4bd2a2cab9ccf78e38`.

The exact transition remains from drifted seed
`a9831e62…4da0` to healthy candidate `fae178a1…0c2` for target
`sa4-lxc104-canary-adapter-v2` only.

## Boundary proof

- production registry v1 still rejects the new target;
- the accepted v2 registry resolves it only at the separate fixed path;
- the v3 owner fails closed on the spent v1 target before any phase begins;
- the v3 runner uses `transaction-input-v2`, `transaction-evidence-v2` and
  `one-use-ledger-v2`, with a distinct operation ID;
- the owner preserves the corrected v2 closed phase graph, complete canonical
  evidence retention, terminal reconciliation and zero-retry rule;
- no credentials, commands, arbitrary target, model or routing surface was
  added.

## Next gate

Prepare an exact reversible inactive-install review for the v3 owner and
runner against fresh LXC 104 facts. Its postcheck may import and validate the
files but must not invoke the runner or create transaction state. A later live
repair still requires fresh unique authority and its own exact effect gate.
