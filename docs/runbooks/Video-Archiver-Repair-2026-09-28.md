# Video archiver repair — 2026-09-28

Owner: Jason. Status: complete — deployed; both retries, Doctor checks and
Jellyfin scan completion verified. Jason explicitly approved the bounded deployment/retry. Maintenance of the
active Stream A [archive compaction project](../projects/Archive-Large-File-Compaction.md).
Jason requested “Can you fix and recheck”; this record defines the concrete repair.

## Findings

- September 28 02:00 compaction: 117 replacements, one failure, one skip,
  one deferred at deadline; 337,972,626,211 → 155,495,408,662 bytes.
- The X-Files (1998) output was 2,000,902,659 bytes, above the 1,995,000,000
  verification limit (1.9 GB cap plus existing 5% tolerance). Original remains
  2,738,281,245 bytes. September 27 Scream 7 failure has the same budgeting cause;
  original remains 3,385,093,856 bytes.
- Both copied audio streams lack stream.bit_rate but carry Matroska BPS tags:
  351,446 and 387,827 bps, respectively. The prior plan assumed 160,000 bps.
- Live Jellyfin is 12.1.0. The configured key matches its existing library-checks
  registration. Read-only authenticated GETs return 401 with X-Emby-Token, 200
  with Authorization: MediaBrowser using the identical key. Scan task exists.
  No secret was printed, exported, changed or rotated.
- Jellyfin 12 disables deprecated authentication by default:
  https://jellyfin.org/posts/jellyfin-release-12.0/

## Candidate and risk assessment

Scope: compact.py and jellyfin_client.py in the existing TrueNAS archiver install,
local Doctor parser and regression tests; retry only the above two failed files,
then request the existing Jellyfin scan and recheck Doctor. No scheduled broad
retry, new service, restart, credential change, firewall/DNS change, Git push or
snapshot deletion is included.

Compaction now reads positive stream bitrate or BPS/BPS-eng statistics, uses a
known audio encoding rate when no rate is available, and reserves 5% planning
headroom instead of 2%. It preserves current file paths, resolution policy,
HDR/audio selection, original-before-verification protection and hard size checks.
Jellyfin requests use the supported Authorization header. Scan failures get a
summary flag/nonzero exit and Doctor counts scan events, without double-counting
the new flag. Existing logs remain intact.

Expected impact: two GPU encodes (about 10–15 minutes total), then a library scan;
no planned service interruption. Successful outputs replace those two originals
only after size, duration, codec, resolution and three decode checks. Space
retention is protected by a new ZFS checkpoint. Main risks are encoding failure,
concurrent execution and rollback storage availability; stop on a changed live
code hash, occupied archiver lock, checkpoint failure or verification failure.

Before deployment capture restrictive code/state checkpoints, prove copies match,
and create a named Media/data repair snapshot. Use a bounded retry runner holding
the existing lock; reuse that checkpoint without invoking snapshot expiry. Retain
all existing snapshots. Restore code from verified checkpoints on deployment
failure; restore only the two media paths from the repair snapshot if necessary,
never roll back the whole shared dataset. Retain logs and checkpoint provenance.

## Validation and resume

- Eleven local regressions pass using an isolated uv environment with requests.
  Tests cover real bitrate metadata, malformed/missing bitrate, surround fallback,
  authorization header and endpoint, rejected scans, Doctor legacy/current schemas,
  empty-detail Bash handling, and scan-only failures without double counting.
- Candidate module evaluated in memory on TrueNAS (no installed code change):
  Scream 7 keeps 1920×800, copied audio/subtitles, 1,726 kbps video;
  X-Files keeps 1920×816 and copied audio, 1,610 kbps video.
  Predicted outputs were about 1.84 GB each; both real outputs passed below.
- Live compact.py SHA256:
  dd69c9e27f2ea0f98d45d5420c9b18ca2be9072cff59604fb087f0448bac2dcb
- Live jellyfin_client.py SHA256:
  8627a5bb4ba0f4153f42f8086e512003456b5354a29199e8b21328fcdc710118
- Lock absent at inspection. Recheck immediately before deployment.

Resume: repair is complete. Retain the checkpoint and snapshot below for recovery;
do not repeat the successful retries. Future nightly runs use the repaired modules.
Git synchronization is outside this repair and remains unapproved.

## Integration impact

Doctor and archiver exit status improve scan-failure visibility. Existing config/
state backup coverage and cron are retained. Operational docs link this repair;
NetBox, topology, Homepage, DNS/firewall, SSO, service identities, broker capability
mapping and credential custody are unchanged. No new service is introduced. Human
wiki/derived Aster knowledge should consume the accepted operational reference
through their normal publication process after live evidence is recorded.

## Approved execution

Jason approved the concrete deployment, checkpoint, two-file retry and recheck.
Started 2026-09-28 13:38 PDT under the archiver lock.

- Checkpoint and durable runner:
  `/mnt/Media/data/tools/video-archiver/work/repair-20260928T203837Z/`
- Snapshot: `Media/data@archive-repair-repair-20260928T203837Z`.
- `status.json` is the authoritative runner phase/result; `runner.log` captures
  progress and `manifest.json` records original file hashes after snapshot proof.
- Existing snapshots retained; the runner substitutes reuse of the verified
  repair snapshot for the normal snapshot/expiry function.

- Scream 7 passed production verification at 13:43 PDT: 3,385,093,856 →
  1,855,778,323 bytes, 1920×800, original selected audio and two English subtitles
  retained; 281 seconds. X-Files retry then started.
- Aster's pinned Doctor exactly matched pre-repair repository HEAD. Installed the
  tested parser after platform approval, with verified rollback at
  `~/Library/Application Support/AsterLab/rollback-doctor-20260928-video-archiver/`.
  No worker restart needed.

## Production verification

The bounded retry completed at 13:48 PDT: two considered, two replaced, zero
file failures, zero scan failures, no skips. Source total 6,123,375,101 bytes →
3,631,195,164 bytes (2,492,179,937 bytes saved before snapshot retention).

| Title | Before | After | Verified output |
|---|---:|---:|---|
| Scream 7 | 3,385,093,856 | 1,855,778,323 | HEVC 1920×800, 7.1 audio, two English subtitles, 6,833.834 s |
| The X-Files | 2,738,281,245 | 1,775,416,841 | HEVC 1920×816, 5.1 audio, 7,361.299 s |

Both outputs passed size, codec, dimensions, duration and three-point decode
checks before replacement. Independent post-run probes confirmed the table.
Original content hashes matched the recovery snapshot before replacement; code/
state checkpoints and isolated code restore copies were verified. Lock released.

Deployed module hashes match the local candidate:
- compact.py: `86a8a27fe24e3754bd2b2ee2fa4d85e711df58456fd8a97f1629dbc01d154916`
- jellyfin_client.py: `07250463de31efbb92021aa5a103f0948d0b3bb1397e0edad04a8c404239180b`

Repository and Aster pinned Doctor each returned:
`PASS video-archiver clean run 0h ago (execute): 2 found, 2 succeeded`.
Both Doctor files match SHA256
`3dcc27bc6c4ed053bdfb767628077a1d5174c14505f25a20838275c598b8156e`.
This is the targeted archiver check, not a claim that unrelated lab checks pass.

Production log: `logs/run-20260928T203853Z.jsonl`. Jellyfin scan requested at
20:48:11 UTC and authenticated task status confirmed it running afterward.

Jellyfin independently reported `Idle`, with `LastExecutionResult.Status=Completed`
for the requested scan: 2026-09-28 20:48:11.9376163Z → 20:50:33.4712101Z
(13:48–13:50 PDT). This confirms completion, not just API acceptance.

Repair complete. No service restarts, credential rotation, schedule changes,
snapshot deletion or Git push. Local source/documentation changes are retained
for commit; remote Git synchronization awaits separate authorization. The repair
snapshot deliberately remains available outside automatic compaction expiry.
