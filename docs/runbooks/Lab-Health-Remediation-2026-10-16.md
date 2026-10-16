# Lab health remediation — 2026-10-16

## Incident

The initial HomeLab Doctor run reported 77 passes, 9 warnings and 3 failures.
The failures were Aster approval readiness, AI-PAM catalogue/socket drift and
an obsolete eight-target Prometheus expectation. Frigate collection timed out,
five configuration backups were stale and the weekly Jellyfin integrity report
had not advanced since 2026-09-23.

This remediation produces no speech and does not change Aster's canonical
voice path.

## Repairs

### Aster approval and AI-PAM

The approval bridge remained active after the main broker restarted, but its
Unix socket pathname had been removed with the shared systemd runtime
directory. An initial unit repair proved that two services cannot safely share
that directory without preservation: restarting the approval bridge restored
its socket but removed the main broker socket.

Both broker units now declare `RuntimeDirectoryPreserve=yes`, and the approval
unit also declares ownership of the shared `homelab-broker` runtime directory.
The main broker's deployed, bounded project-document gateway argument was
reconciled into repository source. The AI-PAM check now includes the deployed
`forgejo-mcp-project-write` service, capability, unit and socket.

After deploying the corrected unit pair and restarting the main broker, both
services were active and both sockets existed with mode `0660` and their
expected groups. Aster approval identity/passkey readiness and the complete
AI-PAM check passed. The protected LXC 104 rollback checkpoint is:

`/root/doctor-repair-20261015T2325PDT/`

### Doctor accuracy and bounded probes

- Prometheus validation now requires exactly nine configured and nine healthy
  targets, matching the live two-voice-endpoint inventory.
- Frigate freshness now inspects only the newest hour directory under today's
  (or yesterday's fallback) recording tree instead of walking the full NFS
  archive. The final probe found a recording less than one minute old.
- Jellyfin integrity now tests its source-local API credential directly and
  reports an authentication failure rather than a misleading stale-report
  warning.

### Recovery exports

Fresh protected configuration exports were captured for OPNsense, Arista,
Proxmox, NUT and Observability. After credential recovery, the Video Archiver
and Jellyfin Integrity exports were also refreshed. Doctor reported all seven
as current.

### Jellyfin integrity recovery

The TrueNAS cron schedule was enabled and launching, but the configured
Jellyfin API keys no longer existed in Jellyfin's registry. Jellyfin 10.11 also
rejects the integrity client's former query-string key transport while
accepting the `MediaBrowser` authorization header.

Two separate replacement keys, `jellyfin-integrity` and `video-archiver`, were
created source-locally without printing or transferring their values. Only the
two protected mode-`0600` configs were updated. Their protected rollback
checkpoint is:

`/mnt/Media/data/tools/credential-rollbacks/doctor-jellyfin-20261016T145921Z/`

The integrity client now uses the authorization header. The live Jellyfin task
inventory also confirmed that the former `Clean up collections and playlists`
task was removed; the guard now distinguishes that safe absence from a changed
ID with re-enabled triggers.

The first authenticated run made one gap-fill correction before encountering
the retired task ID. Its recovery manifest contains one entry and its
destination was verified present. The compatibility-fixed rerun completed in
apply mode, spent 1 of 100 actions, performed its post-apply library scan and
reported zero gap-fill errors, zero collection alerts and no cleanup-task
drift. The final report is:

`/mnt/Media/data/tools/jellyfin-integrity/reports/20261016T150552Z-run.json`

During diagnosis Jellyfin independently performed a clean internal restart and
database migration. No operator restart was issued; readiness returned before
credential changes proceeded.

## Validation

- 26 focused unit/regression tests passed.
- Shell syntax and `git diff --check` passed.
- Final Doctor result: **86 passed, 3 warnings, 0 failures**.

The remaining warnings are bounded and were not silently changed:

1. Eight Aster Wiki sources remain quarantined because their pinned repository
   commits do not match the fetched refs. Updating trust pins requires a
   separate source review.
2. France24 returned one malformed XML response after several successful
   hourly fetches. Other feeds and the aggregator remained healthy.
3. The repository contains pre-existing unrelated uncommitted work.
