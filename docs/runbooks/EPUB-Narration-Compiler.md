# EPUB Narration Compiler Operations

> Status: M3/M4 pilot deployed; worker intentionally inactive
>
> Owner: Jason
>
> Last validated: 2026-10-26

## Safety boundary

The compiler runs locally in unprivileged Aster Speech LXC 116. Proxmox mounts
the Calibre NFS export read-only at `/mnt/epub-calibre-books` and the private
AsterReader export read-write at `/mnt/epub-aster-reader`, then bind-mounts them
into the guest. The compiler identity can read Calibre and write only the
AsterReader dataset. It has no listener, credential, public route or Calibre
write authority. The queue uses SQLite's rollback journal rather than WAL
because its single-writer database is stored on NFS.

Never print or copy book titles, source paths, source text, generated audio,
timing cues, listening progress or source hashes into tickets, Git, Doctor
output or ordinary logs. Use only aggregate state counts and bounded failure
codes.

## Normal status

From the operator Mac, verify the host mounts, monitor timer, worker state and
existing speech services:

```sh
ssh -o BatchMode=yes proxmox "systemctl is-active 'mnt-epub\\x2dcalibre\\x2dbooks.mount' 'mnt-epub\\x2daster\\x2dreader.mount'"
ssh -o BatchMode=yes proxmox "pct exec 116 -- systemctl is-active epub-narration-monitor.timer aster-speech.service aster-voice-candidate.service"
ssh -o BatchMode=yes proxmox "pct exec 116 -- systemctl is-active epub-narration-worker.service 2>/dev/null || true"
```

Healthy pilot state is two active host mounts, an active monitor timer, both
speech services active, and an inactive worker. Read sanitized monitor status
source-locally:

```sh
ssh -o BatchMode=yes proxmox "pct exec 116 -- runuser -u epub-narration -- python3 -c 'import json; d=json.load(open(\"/mnt/aster-reader/state/monitor-status.json\")); print(d[\"state\"],d[\"source_count\"],d[\"queued_new_count\"],d[\"counts\"])'"
```

`lab doctor` checks mount direction, timer/status freshness, queue counts and
the worker's 3 GiB memory, 300% CPU, nice 15 and idle-I/O envelope. A nonzero
failed count is a warning, not permission to print the failed source identity.

## Monitor and worker control

Run one idempotent catalogue reconciliation pass:

```sh
ssh -o BatchMode=yes proxmox "pct exec 116 -- systemctl start epub-narration-monitor.service"
```

Disable automatic discovery without changing queue or output state:

```sh
ssh -o BatchMode=yes proxmox "pct exec 116 -- systemctl disable --now epub-narration-monitor.timer"
```

The worker is not enabled by a timer. Do not start it across the real backlog
until the project records the remaining admission/pause gate. When that gate
is explicitly opened, one manual invocation processes at most one queued
generation:

```sh
ssh -o BatchMode=yes proxmox "pct exec 116 -- systemctl start epub-narration-worker.service"
```

Stop an active attempt with `systemctl stop epub-narration-worker.service`.
Startup recovery records the interrupted bounded failure and requeues it only
while its attempt count remains below the limit. The previous ready generation
is never removed by this operation.

## Failure handling

Failure records contain only an opaque attempt name and one of the bounded
codes: `source-changed`, `unsupported-format`, `epub-invalid`,
`voice-contract`, `timing-invalid`, `quota`, `publish` or `interrupted`.

- `source-changed`: run the monitor again; it creates the new generation key.
- `epub-invalid`: quarantine for human compatibility review; do not loosen ZIP
  or XML limits globally.
- `voice-contract`: keep the worker stopped and verify model, voice pack,
  cleanup hash and execute-only ACLs.
- `timing-invalid`: preserve the last-known-good pointer; do not interpolate or
  downgrade the timing gate.
- `quota`: keep the worker stopped and review the 128 GiB dataset quota and
  retained generations. Never delete the only ready generation.
- `publish`: validate staging/generation state and the ready pointer before an
  explicit bounded retry.

After correcting the cause, retry exactly one bounded failure class. The tool
prints only the aggregate number requeued and refuses attempts already at the
cap:

```sh
ssh -o BatchMode=yes proxmox "pct exec 116 -- runuser -u epub-narration -- env PYTHONPATH=/opt/epub-narration python3 /opt/epub-narration/tools/retry_failures.py --state-root /mnt/aster-reader/state --failure-code quota"
```

## Backup and recovery

The full `Media/AsterReader` dataset has a daily 04:45 snapshot task with
14-day retention and no empty snapshots. The protected configuration exporter
also captures an online SQLite backup of `state/queue.db`, status files, ready
pointers and immutable manifests. It deliberately excludes reproducible Opus
and timing payloads. The encrypted/off-site configuration path therefore
preserves orchestration and identity while local ZFS snapshots cover bulk
generated data.

Validate backup coverage with:

```sh
python3 scripts/check-configuration-backups.py
```

Restore into an isolated dataset or directory first. Verify the SQLite
integrity check, manifest hashes and ready pointers there; never overwrite the
live dataset as the first restore step. Source EPUBs remain authoritative, so
missing bulk narration is regenerated only after the isolated state restore
passes.

## Rollback

1. Disable the monitor timer and stop the worker.
2. Confirm both speech services remain active.
3. Retain the AsterReader dataset, snapshots and queue; do not delete output.
4. Remove any future staged Aster Books ready-root reference. M3/M4 added none.
5. If guest deployment itself must be reverted, use LXC snapshot
   `epub-narration-m3-pre-20261026`; separately disable the two Proxmox mount
   units and remove `mp0`/`mp1` only after the guest is stopped.
6. If backup-export code must be reverted, restore the protected appdata
   snapshot `Media/appdata@epub-backup-pre-20261026` to an isolated location
   and replace only the exporter after comparison.

Rollback never writes to Calibre and never deletes the last ready generation.
