# Stream A F6 inactive installation transaction

Status: **PREPARED ONLY; DO NOT EXECUTE WITHOUT SEPARATE EXACT APPROVAL**

This transaction stages the accepted 13-artifact F6 watchdog/recovery packet
while keeping every service and timer disabled and inactive. It must be
executed as one bounded transaction after a fresh read-only preflight. It does
not create an owner identity, owner intent, lease, lock, heartbeat, status or
restore-intent file and it never invokes the restore observer.

## Pinned inputs

- Accepted implementation: `780c33e2471536ff0f3eb699a9dba93274808919`.
- Accepted metadata/card: `75b423d43c00611681c5e68ed07e3535c171ceb2`.
- Card SHA-256: `78fd2388168c464877c20b7abab3f99f042bb553de38f7f56d46227ef8d99210`.
- Manifest: `STREAM-A-EVALUATION-LEASE-F6-INACTIVE-INSTALL-MANIFEST-20261025.tsv`.
- Manifest contains exactly 13 target artifacts: four Python files, four
  wrappers and five systemd unit/timer files.

## Required preflight checkpoint

Before any copy, record a root-owned checkpoint containing:

1. The exact six existing dependency files and hashes:

   - `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py`
     — `675ebb566de298334f7c612cae9af2637067930f40c0ad2c23a22e1b7e248f1b`.
   - `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py`
     — `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1`.
   - `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py`
     — `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725`.
   - `/usr/local/libexec/local-ai-lease/stream-a-evaluation/host_exclusion.py`
     — `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61`.
   - `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py`
     — `e4efd62036b8d26b0eb972a03f53f2cfdf6fbb6fa8a00f1c652b5803c23b5ce7`.
   - `/usr/local/sbin/stream-a-evaluation-lease`
     — `962100b591493b2ae8f62814fa6f66a1875463dd5ca613bb321169764c56c276`.

2. Absence of all 13 manifest targets, with the existing dependency root
   still `root:root 0755`; no target may be a symlink or non-regular file.
3. Existing owner, watchdog and heartbeat unit/timer state remains disabled and
   inactive; no target process, lease, lock, identity, intent, heartbeat,
   status, observer output or `.pyc` exists.
4. The accepted backend, four production consumers, F2 timers, schedules,
   GPU holder and backup state are unchanged. No evaluation or model request
   is running.

The checkpoint is a no-go if any target exists, any dependency hash drifts, or
any runtime state is present. Do not overwrite an existing target.

## Copy order

1. Verify the clean source commit and manifest hashes from a hierarchy-preserving
   archive. Verify the archive contains no credentials, runtime state, identity,
   intent or compiled bytecode.
2. Create only the already-known source root if absent, preserving its required
   `root:root 0755` custody. Copy the four Python files into that root with
   `root:root 0644`.
3. Copy the four wrappers to `/usr/local/sbin` with `root:root 0755`.
4. Copy the five unit/timer files to `/etc/systemd/system` with `root:root
   0644`. Do not run daemon-reload, enable, start, arm, or invoke any wrapper.
5. Rehash every target, verify regular-file/no-symlink type and exact custody,
   and retain the checkpoint until postflight is complete.

## Inactive postflight

- Run imports and the accepted focused test set with Python `-B`.
- Invoke only the three inert wrappers (owner, owner-heartbeat and watchdog)
  without effect authorization; require the exact disabled response.
- Do not invoke the restore-observer wrapper: it is separately gated and its
  authorized path makes the bounded authentication probe/model request.
- Verify all five units/timers are disabled and inactive, with no
  `daemon-reload`, no lease/lock/identity/intent/heartbeat/status files, no
  observer output and no `.pyc`/`__pycache__`.
- Recheck backend, consumers, schedules, GPU holder, F2 timers and backup
  state read-only. Any drift is a failed transaction.

## Rollback artifact and decision

On any copy, hash, custody, unit-state or postflight failure, stop the
transaction and remove only the 13 newly added targets after confirming each
target still matches the manifest. Do not remove or rewrite the six existing
dependency files. Do not run systemd reload/disable/stop commands because the
units were never enabled or started by this transaction.

If any target identity or runtime state is uncertain, retain the root-owned
checkpoint and uncertain files for manual reconciliation; do not retry
automatically. The transaction is successful only when all 13 targets match,
all units/timers are disabled/inactive, and all runtime-state absence checks
pass. Installation approval does not authorize F6 activation; timer arming,
identity creation, owner-process start, lease acquisition and recovery remain
separate approvals.
