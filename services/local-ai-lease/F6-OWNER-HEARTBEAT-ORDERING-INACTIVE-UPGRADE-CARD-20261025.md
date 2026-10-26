# F6 owner-heartbeat ordering — inactive unit upgrade

Status: **SOURCE READY; INSTALLATION NOT AUTHORIZED**

The installed heartbeat service requires the persistent evaluation owner, but
does not order itself after that owner. Since the heartbeat service condition
depends on the identity written by the owner, parallel startup can skip the
first heartbeat. The candidate adds only the missing systemd ordering edge.

| Target | Installed SHA-256 | Candidate SHA-256 | Mode |
|---|---|---|---:|
| `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.service` | `6c7777506df7aa2b58e62e3da7fb354859b6487e99441b4445c8a2a537df2ad5` | `7bbb32a64a73b8797f34df934f9f06932c0706f93dc078b08bbc2c737d364f1e` | `0644` |

The only source diff is:

```diff
-After=local-fs.target
+After=local-fs.target stream-a-evaluation-owner.service
```

## Inactive transaction

1. Require the exact installed prestate, root ownership, mode `0644`, one
   regular link, lease `ready`, no evaluation state/lock/process, and every F6
   unit/timer disabled and inactive. Preserve the October 26 F2 timers.
2. Preserve the old unit in a new root-owned mode-`0700` checkpoint. Stage the
   candidate separately and run `systemd-analyze verify` against the owner,
   heartbeat and watchdog unit set before replacement.
3. Replace only the heartbeat service as `root:root 0644`, daemon-reload, and
   re-run `systemd-analyze verify` plus the source unit regression tests.
4. Recheck exact hash/custody, F6 disabled/inactive, lease ready, no runtime
   state and unchanged enabled/active October 26 F2 timers.

Rollback restores the one checkpointed unit, daemon-reloads and repeats the
same disabled/inactive and schedule checks. This upgrade must not enable or
start the owner, heartbeat or watchdog, write an identity, acquire a lease,
stop a consumer, invoke recovery, call a model or alter F2/F3.
