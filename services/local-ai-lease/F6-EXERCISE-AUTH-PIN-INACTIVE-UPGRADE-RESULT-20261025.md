# F6 prepare-only exercise auth-helper pin — inactive upgrade result

Status: **PASS — INSTALLED INACTIVE**

Jason approved the one-file replacement described by card commit `6222003c`.
The installed prepare-only runner now matches source commit `d4473311` and
recognizes the corrected negative-control authentication helper.

## Installed identity and rollback

| Target | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_prepare_only_exercise.py` | `29429e7f5ff5252fed46b9cf27865d29ea1d891d14472739a056dc1ecc0eaa1e` | `root:root 0644`, regular, one link |

The prior runner with SHA-256
`cf51b1d6546e27aebdef9e44ad4751343e38aa388c8eae682f9a476641f390fb`
is preserved mode `0600` beneath the root-owned mode-`0700` checkpoint
`/var/lib/local-ai-lab/checkpoints/f6-exercise-auth-pin-d4473311-20261025`.

## Validation

- The corrected complete target fixture passed 94/94 tests.
- Installed-path import passed with bytecode creation disabled.
- Inert invocation returned exactly `{"effects": "disabled", "state":
  "source-only"}`.
- The installed LXC110 auth helper remained at
  `93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582`.
- The lease remained `ready`; no lease, lock, runtime state, receipt or F6
  process appeared.
- All F6 units remained absent/inactive. The October 26 F2 prepare/final
  timers remained enabled and active; their recurring counterparts remained
  disabled and inactive.

The first remote test invocation used an incomplete fixture containing only
`scripts/local-ai` and therefore reported seven missing-wrapper path errors.
No runtime effect was attempted. Repacking the same source with its
`services/local-ai-lease` wrappers produced the required 94/94 result. A
subsequent direct execution attempt correctly failed because the installed
Python source is deliberately non-executable mode `0644`; invoking it through
Python produced the exact inert result above.

This closes the stale downstream helper pin only. It does not arm F6, acquire
a lease, stop a consumer, call a model, create F4/F5 evidence or alter F2/F3.
