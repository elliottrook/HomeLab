# F4/F5 metadata-only authentication — inactive upgrade result

Status: **PASS — INSTALLED INACTIVE**

Jason approved the exact two-file upgrade from source tip `76072b38` and card
commit `c82b3fb0`. The correction was independently reviewed GO after its first
version was rejected because `/v1/models` acceptance alone did not prove
authentication.

## Installed identities

| Target | SHA-256 | Custody |
|---|---|---|
| LXC110 `/usr/local/libexec/aster-a1/llama_auth_probe.py` | `93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582` | `root:root 0644`, regular, one link |
| Proxmox `/usr/local/libexec/local-ai-lease/trusted_observer.py` | `6091b5572764abf3675d9140e760083a1482fee8abfef8fc763fb72853618f5f` | `root:root 0644`, regular, one link |

Both prior files and their hashes are preserved in root-owned mode-`0700`
checkpoint
`/var/lib/local-ai-lab/checkpoints/f4-f5-auth-metadata-76072b38-20261025`.

## Validation

- The corrected helper passed 4/4 target-Linux unit tests.
- The corrected observer passed 9/9 target-Linux unit tests.
- The live GET-only helper required no-auth `401`, fixed-invalid `401`, then
  valid-key `200` with the exact model and exited zero. It sent no inference
  body and printed no credential or response content.
- The installed observer's exact fixed auth command returned only
  `auth-metadata-ok`.
- The lease remained `ready`, both October 26 F2 timers remained active, the
  cycle state and retained receipt remained absent, and no archive scanner ran.
- No service was restarted and no model request was sent.

This result corrects only future F4/F5 authentication evidence. It does not
produce F4/F5, acquire a lease, arm F6, stop production or authorize candidate
H. The inactive F6 exercise runner still pins the superseded helper hash; local
source commit `d4473311` corrects that downstream pin and requires its own
inactive installation before another F6 exercise.
