# F4/F5 metadata-only authentication — inactive upgrade card

Status: **SOURCE REVIEW GO; INSTALLATION NOT AUTHORIZED**

The existing trusted observer proves authentication by sending a one-token
completion. This contradicts the F4/F5 no-model-call boundary. The corrected
pair requires `/v1/models` to reject both no authorization and a fixed invalid
bearer before accepting a real key and returning the exact model. All requests
are GET-only and contain no inference body.

Independent review accepted source tip `76072b38`. The combined auth,
observer, pre-acquire, controller and admission suite passed 39/39 locally.
The corrected helper also passed once from temporary LXC110 storage against
the live service without a model request.

## Exact replacements

| Source | Target | Prestate SHA-256 | Candidate SHA-256 |
|---|---|---|---|
| `scripts/local-ai/llama_auth_probe.py` | LXC110 `/usr/local/libexec/aster-a1/llama_auth_probe.py` | `0996e1b565ad24b740997bbfe598065267e20380135a5af41687d0562239cae6` | `93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582` |
| `scripts/local-ai/trusted_observer.py` | Proxmox `/usr/local/libexec/local-ai-lease/trusted_observer.py` | `de6d2da913a1dab4f5e371739a6a3eada79b99d8e11e2d3b64cf0f825274074e` | `6091b5572764abf3675d9140e760083a1482fee8abfef8fc763fb72853618f5f` |

Both current targets are `root:root 0644` regular one-link files. The observer
pins the candidate helper hash and fixed guest path.

## Bounded inactive transaction

1. Recheck both prestates and the candidate/test hashes. Require no active
   lease, lock, F2/F3 process, archive scan or competing maintenance.
2. Create root-owned mode-`0700` checkpoint
   `/var/lib/local-ai-lab/checkpoints/f4-f5-auth-metadata-76072b38-20261025`
   and preserve both prior files plus a hash inventory before replacement.
3. Replace only the two targets as `root:root 0644`, then verify candidate
   hashes, regular-file type and one link.
4. Run the four helper tests in LXC110 and the nine trusted-observer tests on
   Proxmox from complete temporary fixtures with bytecode disabled. Run the
   corrected helper once against live `/v1/models`; it must exit zero after
   observing no-auth `401`, fixed-invalid `401`, and valid-key `200` with the
   exact model. Retain only exit state, never credentials or response content.
5. Recheck production and F2 timers, no lease/lock/receipt/process, and no
   model request. Do not restart any service or enable any unit.

Any hash, custody, test, service or negative-control discrepancy restores both
checkpointed files before reporting failure. If rollback is uncertain, retain
the checkpoint and stop; do not claim the old pair was restored.

This upgrade does not produce F4/F5 evidence, write an admission artifact,
acquire a lease, stop a service, call a model, alter F2/F3, arm F6 or authorize
candidate H. It only makes the future authentication observation truthful and
non-inferential.
