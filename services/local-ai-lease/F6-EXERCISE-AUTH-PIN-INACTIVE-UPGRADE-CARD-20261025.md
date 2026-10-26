# F6 prepare-only exercise — corrected auth-helper pin inactive upgrade

Status: **SOURCE READY; INSTALLATION NOT AUTHORIZED**

The installed F6 prepare-only exercise runner differs from source commit
`d4473311` in exactly one line: it pins the superseded LXC110 auth helper. The
helper itself is now installed at the corrected negative-control hash. This
card replaces only the runner so the future inert F6 preflight can recognize
that helper.

| Target | Prestate SHA-256 | Candidate SHA-256 | Mode |
|---|---|---|---:|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_prepare_only_exercise.py` | `cf51b1d6546e27aebdef9e44ad4751343e38aa388c8eae682f9a476641f390fb` | `29429e7f5ff5252fed46b9cf27865d29ea1d891d14472739a056dc1ecc0eaa1e` | `0644` |

The measured installed/source diff is only the helper SHA-256 transition from
`0996e1b565ad24b740997bbfe598065267e20380135a5af41687d0562239cae6`
to `93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582`.

## Inactive transaction

1. Recheck the runner prestate and installed helper hash. Require lease ready,
   all F6 units/timers disabled/inactive, no F6 runtime state, and no competing
   F2/F3 process.
2. Preserve the old runner in a new root-owned mode-`0700` checkpoint, replace
   only this file as `root:root 0644`, and verify its exact hash/custody.
3. Run the nine prepare-only runner tests plus the complete exercise, owner,
   watchdog, restore-observer, lease, adapter, entrypoint, auth and trusted-
   observer suite; require the 94-test baseline.
4. Run only the runner's inert default invocation and installed-path import.
   Recheck no lease, lock, identity, heartbeat, receipt, service command or
   model request and unchanged F2 timers.

Rollback restores the one checkpointed runner after exact hash verification.
This upgrade does not run an exercise, enable F6, acquire a lease, stop a
consumer, call a model, create F4/F5 evidence or alter F2/F3.
