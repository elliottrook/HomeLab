# EPUB Narration Compiler Operations

> Status: M5 pilot deployed; worker intentionally inactive; Aster Books beta inactive
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

Ready generations also contain a private normalized chapter document under
`content/`. It is hash-bound to both the manifest and timing document so Aster
Books can highlight the exact sentence being spoken. Treat it as source text:
it is covered by local dataset snapshots and deliberately excluded from the
configuration archive, ordinary diagnostics and Aster's knowledge corpus.

## Inactive Aster Books beta

The HP lab appliance has an immutable synthetic beta at
`/storage/.aster-staging/aster-books-compiler-beta1`. Its bundle manifest must
say `active=false`, `production_entry=false`, `network=false` and
`shared_progress=false`. It is not linked from the skin, add-on registry or a
service. It validates only complete atomic ready generations and stores
generation-bound progress in a private owner-only directory.

The beta's recovery checkpoint is
`/storage/.aster-checkpoints/aster-books-compiler-beta1-20261026`. Removing the
single staged bundle directory returns to the exact pre-M5 state; do not touch
the existing historical EPUB preview or its separate progress. Production
BOSGAME remains unchanged and needs its own explicit promotion checkpoint.

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

Validate an archive through an isolated temporary restore without emitting
private records:

```sh
python3 scripts/backup/verify-epub-narration-restore.py /path/to/configs.tar.gz
```

The result contains only the queue-record, ready-pointer and generation-
manifest counts plus the media-exclusion decision. A zero ready/manifest count
is expected while the real worker remains inactive.

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
5. Remove the inactive HP beta directory only after verifying its dedicated
   absent-state checkpoint. It has no normal-route reference to remove.
6. Restore the pre-M5 renderer from
   `/opt/epub-narration/rollback-m5-20261026/renderer.py` and remove only the
   added `aster_books.py` consumer if the M5 compiler interface must be
   reverted. Keep the worker inactive during comparison.
7. If the broader guest deployment must be reverted, use LXC snapshot
   `epub-narration-m3-pre-20261026`; separately disable the two Proxmox mount
   units and remove `mp0`/`mp1` only after the guest is stopped.
8. If backup-export code must be reverted, restore the protected appdata
   snapshot `Media/appdata@epub-backup-pre-20261026` to an isolated location
   and replace only the exporter after comparison.

Rollback never writes to Calibre and never deletes the last ready generation.
