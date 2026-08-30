# Surveillance

**Status:** Operational pilot  
**Last updated:** 2026-08-30

## Components

| Component | Location | Address |
|---|---|---|
| Frigate | Proxmox VM 102, Servers VLAN 20 | `192.168.20.10` |
| Reolink Duo 2V PoE | Cameras VLAN 60 | `192.168.60.10` |
| Recording storage | TrueNAS NFS | `/mnt/Media/Surveillance/Frigate` |

Frigate runs in Docker Compose under `/opt/frigate`. Its authenticated web UI
is published on TCP 8971. The camera provides HTTP management on TCP 80, RTSP
on TCP 554 and ONVIF on TCP 8000. OPNsense permits only those three ports from
the Frigate host to the camera.

## Streams and recording

- Main stream: 5120x1552, 20 FPS, HEVC/AAC; recording and audio roles.
- Substream: H.264/AAC; detection role.
- Continuous retention: 3 days.
- Motion retention: 7 days.
- Alert and detection retention: 30 days in motion mode.
- Hardware acceleration is not yet configured; CPU detection is acceptable
  for the single-camera pilot but is not the final scaling design.

## Detection triggers

As of 2026-08-30, `objects.track` is explicitly scoped to `person` and `car`
(previously unset, which tracked every COCO label the Coral model supports
with no filtering). Three zones are defined on `front_of_house`, in the
camera's `detect` coordinate space (1920×576):

- `driveway` — the paved parking area, from the street edge to the house.
- `porch` — the immediate foreground behind the porch railing, closest to the
  camera; the highest-priority zone for person detection.
- `street` — the road and parked cars across the street; background/lower
  priority.

`review.alerts` fires only for `person`/`car` inside `driveway` or `porch`.
Everything else (e.g. a car passing on `street`) logs as a `detection`
instead — same retention (30 days, motion mode), lower review priority. There
is no MQTT/Home Assistant integration yet (Milestone 4, not started), so
"finding" a trigger currently means browsing Frigate's own Review/Explore UI,
not an external notification.

`face_recognition` and `lpr` (license plate recognition) were found already
enabled (small models) outside the documented process — likely turned on via
the Frigate setup wizard — and were disabled 2026-08-30 pending a scoped
privacy/retention decision, then deliberately re-enabled later the same day
once that decision was made (full rationale in
[Surveillance-Expansion.md](projects/Surveillance-Expansion.md) Milestone 5):
both run at the camera level in Frigate with no way to restrict them to the
`driveway`/`porch` zones, so they process everyone visible anywhere in
frame, including public-street passersby and traffic — a knowingly accepted
tradeoff, not an oversight. Face recognition still needs reference photos of
known household members added through Frigate's Face Library UI before it
can distinguish anyone by name. `semantic_search` (embedding-based search,
not identity recognition) remains enabled and was not part of either
decision.

**Critical finding, 2026-08-30: object detection had never actually run.**
While validating the trigger config above, `event`/`reviewsegment`/`regions`
all showed zero rows — not just since today's restart, but for the entire
database history back to its creation on 2026-08-09. Motion detection,
recording, the Coral TPU, and the model were all confirmed healthy throughout
(TPU found at startup, steady ~10ms inference, motion boxes correctly
tracking real movement in the debug view) — the actual cause was that each
camera's **`detect` toggle is a runtime/session setting Frigate keeps
separate from `config.yaml`**, not persisted across restarts because
`mqtt.enabled: false` (MQTT retained messages are Frigate's usual mechanism
for persisting that toggle). It silently defaulted to *disabled* on every
restart, including today's two — enabling it via the Live view UI worked
immediately (confirmed via the debug overlay: correctly labeled, scored,
tracked `car`/`person` boxes) but reverted to disabled on the next restart.
Fixed by explicitly setting `detect.enabled: true` under the camera in
`config.yaml`, confirmed to survive a restart and produce real events zoned
correctly (`person` in `porch`/`driveway`, `car` in `driveway`/`street`).
**Any future camera onboarded via the runbook must set this explicitly** —
see [10-Camera-Onboarding-Runbook.md](10-Camera-Onboarding-Runbook.md).
This also means every prior "stable" observation of this camera (the
2026-08-11/12 and 2026-08-16 checkpoints, and the original single-camera
baseline sign-off) validated recording and storage only, not detection —
worth keeping in mind when reading those as evidence of readiness.

The full step-by-step procedure for replicating this trigger pattern on a new
camera is in
[`docs/10-Camera-Onboarding-Runbook.md`](10-Camera-Onboarding-Runbook.md).

## Known issues

### Record-stream segment fragmentation (resolved 2026-08-30)

**Status:** Resolved. Not a bug in the end — a mismatch between Frigate's
default `segment_time: 10` and this camera's hardware-capped ~2-second
keyframe interval. Fixed by setting Frigate's segment length to match the
camera's actual cadence instead of fighting it. Confirmed: segments are now
uniform (~718-725KB, tight and consistent, vs. the previous erratic
716KB-4.2MB range) and the clip that previously failed to decode
(`VTDecompressionOutputCallback`) now plays cleanly.

**Symptom:** The `front_of_house` record-role ffmpeg process (writes
10-second `-f segment` MP4s from go2rtc's local main-stream restream, using
`-c:v copy`) intermittently produces fragmented segments as short as ~2
seconds instead of the expected ~10, for extended periods (one stretch ran
nearly 80 minutes continuously). Segment sizes drop correspondingly
(~850KB-1.3MB fragmented vs. ~3.1-3.6MB for a proper 10s segment). Frigate's
own storage anomaly detector flagged this directly at a restart:

```
frigate.storage WARNING : front_of_house has a bandwidth of 25178.17 MB/hr
which exceeds the expected maximum. This typically indicates an issue with
the cameras recordings.
```

~25 GB/hr against the documented normal of ~1.43 GiB/hr — roughly 17x over.

**Impact observed:**
- One clip (~11:23 local, 2026-08-30) failed to play in the Frigate UI with a
  client-side decode error (`PIPELINE_ERROR_DECODE` /
  `VTDecompressionOutputCallback (-12909)` in Safari on macOS), consistent
  with a malformed/truncated segment.
- Frigate's own watchdog separately triggered an automatic record-ffmpeg
  restart at 11:57:27 after 120s with zero new segments — a related but
  distinct symptom (a brief full stall, not fragmentation).
- Frigate's own bandwidth estimate (used for storage/retention projections)
  was thrown off by ~17x during the affected period.

**What's been ruled out:**
- The detect substream (`Preview_01_sub`) is unaffected — motion and object
  detection both worked flawlessly throughout, including during fragmentation
  windows. This isolates the fault to the main/record stream path
  specifically, not the camera or network being broadly unhealthy.
- Not inherited container/process state from Claude Code's restarts — the
  pattern began 46 seconds after the first restart that day but survived a
  **full stack teardown and rebuild** (`docker compose down` + `up`, not just
  `systemctl restart frigate-compose.service`) with no change. The
  correlation with that first restart is more likely coincidental with
  daytime activity starting than causal.
- The camera's own encoder settings, queried directly via its HTTP API
  (`GetEnc`) from the already-authorized Frigate host, look reasonable, not
  misconfigured: main stream 5120x1552 H.265, 7168 kbps, GOP=2 (2s keyframe
  interval); substream 1920x576 H.264, 1024 kbps, GOP=4.

**Leading theory (unconfirmed):** ffmpeg's `-f segment -segment_time 10
-c:v copy` muxer can only cut a new segment at a keyframe boundary. With a
2-second GOP, a healthy segment should land around 10-12s (waiting for ~5
keyframes). Segments cutting at ~2s — i.e., at every keyframe instead of
every fifth — suggests ffmpeg's internal elapsed-time tracking for the
segment boundary is being reset or confused, plausibly by PTS/timestamp
irregularities somewhere in the RTSP → go2rtc-local-restream → ffmpeg chain,
possibly exacerbated during higher-motion daytime periods. The exact trigger
for the ~10:36 local onset isn't confirmed; daytime motion/bitrate demand is
a plausible but unproven correlation.

**What would help next:**
- Verbose/debug ffmpeg stderr for the record-role process specifically —
  not available through current log access (Frigate's log tabs don't surface
  per-process ffmpeg stderr at useful detail, and this account has no
  `docker logs`/`journalctl` access on the Frigate VM).
- A longer observation window correlating fragmentation windows against
  measured network throughput/motion levels, to test the daytime-bitrate
  theory.

**GitHub research (2026-08-30):** checked ~10 Frigate/go2rtc issues (segment
cache warnings, GOP/keyframe problems, HEVC issues), including one
specifically about Reolink Duo cameras (`blakeblackshear/frigate#8128`) —
same camera family as `front_of_house`. No exact match for this symptom
(segments cutting at every keyframe instead of every fifth), but that thread
shows other Reolink Duo owners tuning I-frame interval specifically for
Frigate reliability, and general friction with this camera family's
H.265/H.264 stream handling — corroborating, not conclusive.

**GOP-interval experiment attempted, blocked (2026-08-30):** tried raising
the main stream's GOP from 2 to 10 via the camera's own `SetEnc` CGI API
(`http://192.168.60.10/cgi-bin/api.cgi`), reachable from the already-
authorized Frigate host using the same admin credentials embedded in
Frigate's config. `GetEnc`/`Login` both worked correctly (confirmed via a
deliberate auth-failure test — using a cookie instead of the query-string
token correctly produced a *different* "please login first" error,
confirming the query-string token method truly authenticates). `SetEnc`
itself was rejected with a generic `err get data from json` (rspCode -56)
across four structurally different, valid JSON payloads (with/without the
redundant `size` field, with/without `action`). This looks like the
camera's firmware doesn't support this specific write via the public CGI
API — Reolink's official app may use a different, undocumented protocol.
The camera has no other reachable admin path from any device except Frigate
(VLAN 60 isolation), so confirming this needed a temporary, deliberate
firewall exception (Trusted VLAN → camera, port 80, single host, removed
immediately after use) to reach the camera's native local web UI directly.

**GOP experiment closed, conclusively — not a config gap, a hardware/firmware
ceiling (2026-08-30):** the camera's own UI confirms `I-frame Interval` for
the main/record stream ("High Clear," 5120×1552) only offers `1x` or `2x` as
valid options — `2x` (the current, already-live value) is the maximum this
stream profile supports. This retroactively explains every `SetEnc` API
failure above: the request wasn't malformed, it was asking for a value
(`gop: 10`) outside the camera's accepted range for this stream. There is no
room to raise this setting further, on this camera, via any interface — so
the fix had to come from the Frigate side instead.

**Fix applied (2026-08-30):** overrode the record-role ffmpeg command for
`front_of_house` via `cameras.front_of_house.ffmpeg.output_args.record` in
`config.yaml`, changing only `-segment_time 10` to `-segment_time 2` (kept
every other flag identical to Frigate's default:
`-f segment -segment_time 2 -segment_format mp4 -reset_timestamps 1
-strftime 1 -c:v copy -c:a aac`). Backup: `config.yaml.before-segmenttime-*`.
Rationale: with `-c:v copy`, ffmpeg's segment muxer can only cut at a
keyframe, and this camera's main stream is hardware-capped at a ~2s keyframe
interval (see GOP finding above) — asking for a 10s segment meant ffmpeg had
to reliably wait for and count five consecutive keyframes before cutting,
which its internal elapsed-time tracking apparently couldn't do reliably
(the likely source of both the fragmentation and the one corrupted clip).
Asking for exactly one keyframe's worth of duration removes that multi-
keyframe counting dependency entirely. Restarted and confirmed: uniform
~2-second segments (~718-725KB, a tight band vs. the previous erratic
716KB-4.2MB spread) and the previously-corrupted clip's time range now plays
back cleanly with no decode error. Tradeoff accepted: more, smaller files on
disk than originally intended — not expected to matter for a single camera
at this storage scale (11 TB available, ~26 GB used as of this session).

## Storage and boot ordering

The TrueNAS export is mounted at `/opt/frigate/storage` using NFSv4 with a hard
mount and systemd automount. `frigate-compose.service` triggers and verifies the
real NFS mount before Compose starts. This prevents Docker from binding the
autofs placeholder or an empty local directory during boot.

After reboot, validate:

```sh
findmnt -rn -t nfs4 -T /opt/frigate/storage
systemctl is-active frigate-compose.service
cd /opt/frigate
sudo docker compose ps
sudo find /opt/frigate/storage/recordings -type f -mmin -3 | head
```

Expected results are an NFSv4 source from `192.168.20.40`, an active systemd
unit, a healthy Frigate container and recent MP4 recording segments.

The TrueNAS address migration was validated with a complete Frigate VM reboot on 2026-08-16. The systemd automount resolved to the new source, `frigate-compose.service` became active, the container reported healthy with zero restarts, and fresh recording segments appeared on the NFS export.

## Stability checkpoint

The 2026-08-11 observation found a healthy container with zero restarts, fresh
recording segments on the TrueNAS NFS export and no recording interruptions in
the final 24 hours. The VM had 5.7 GiB RAM, 4.2 GiB available and effectively no
swap use; the Frigate container used about 1.4 GiB RAM and 11% CPU during the
sample. The NFS dataset reported 47 GiB used of 11 TiB.

Configured retention remains three days continuous, seven days motion and 30
days for alerts/detections. On 2026-08-12 the database and recording filesystem
were inspected after the three-day boundary: only one continuous-only segment
was slightly beyond 72 hours while motion-bearing segments correctly remained
under the seven-day policy. This is consistent with periodic automatic cleanup,
so retention validation is complete without force-deleting recordings.

## Recovery and backup

The configuration backup includes the Compose file, Frigate configuration,
systemd startup unit and `/etc/fstab`. It excludes recordings. Because camera
credentials are present, the archive must remain private, use restrictive file
permissions and never be committed to Git.

If Frigate is down after boot, check the mount before restarting the stack:

```sh
findmnt -T /opt/frigate/storage
systemctl status frigate-compose.service --no-pager -l
journalctl -b -u frigate-compose.service \
  -u opt-frigate-storage.mount \
  -u opt-frigate-storage.automount --no-pager
```
