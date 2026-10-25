# Stream A exercise-owner runtime directory — inactive custody card

Status: **INSTALLED AND VERIFIED; RETRY REQUIRES NEW APPROVAL**

The second live exercise attempt failed closed before owner identity or
watchdog action because the transient unit's pinned `ReadWritePaths` directory
`/etc/local-ai-lab/stream-a-evaluation` was absent. The prepared lease was
cancelled safely and all runtime state is absent. This card defines only the
bounded static directory prerequisite; it authorizes no exercise retry,
service start, lease, model call, consumer mutation, timer change or push.

## Verified custody result

The target directory was created empty as `root:root` mode `0700`; its parent
remained `root:root` mode `0700`. The exact transient namespace check completed
successfully in 35ms with exit `0`, was collected to `LoadState=not-found`, and
left the directory empty with no owner or runtime state. Fresh full prestate
passed with exact guest pins, whole-host lease ready, F6 inactive, four healthy
consumers, metadata-only auth/idle, accepted GPU holder and unchanged October
26 F2 timers at 01:15/01:20 PDT. No exercise retry occurred; any new attempt
requires separate approval.

## Exact static-custody transaction

Target: `/etc/local-ai-lab/stream-a-evaluation`

Required final state: root-owned directory, mode `0700`, empty, no symlink.
The parent `/etc/local-ai-lab` must retain its existing custody and mode.

## Required sequence

1. Capture parent and target prestate: existence, type, symlink status, owner,
   mode and content listing. Refuse on an existing non-directory, symlink,
   unexpected owner/mode or any non-empty target.
2. If absent, create only the target directory atomically enough for the host
   platform, set `root:root` and mode `0700`, then recheck no files exist.
   Do not create identity, intent, lease, lock, heartbeat, receipt, unit or
   timer state.
3. Validate namespace entry with a unique transient validation unit, not the
   owner wrapper, using the exact bounded command shape:

   `/usr/bin/systemd-run --unit=stream-a-evaluation-exercise-path-check.service --collect --wait --property=User=root --property=NoNewPrivileges=yes --property=ProtectSystem=strict --property=ProtectHome=yes --property=PrivateTmp=yes --property=ReadWritePaths=/etc/local-ai-lab/stream-a-evaluation /usr/bin/test -d /etc/local-ai-lab/stream-a-evaluation`

   Require exit `0` and result `finished`; then prove the transient unit is
   absent/collected and the directory remains empty. This command must run no
   owner executable, write no identity/intent, create no lease, call no model,
   and enable or arm no timer.
4. Recheck all F6 units/timers, four consumer states, F2 timer identities and
   whole-host lease. Record only hashes/custody/results; do not retry the
   consumed live approval.

## Rollback

Remove the target directory only when it was absent before the transaction and
is still empty, root-owned, mode `0700`, and not a symlink. If it contains any
file or custody has drifted, retain it and stop for manual reconciliation.
Never remove the parent directory or any pre-existing path.

The second live attempt's prepared lease
`exercise-20261025-1792967951-1d319b6d` was cancelled before its restore
deadline with `cancelled-prepared`; final lease/lock/identity/heartbeat/status/
receipt state was absent, F6 remained disabled/inactive, consumers and F2 were
unchanged, and the whole-host lease remained ready.

This card is a prerequisite for any future separately approved retry and is
not authorization to execute one.
