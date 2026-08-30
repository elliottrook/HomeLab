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
privacy/retention decision (tracked in
[Surveillance-Expansion.md](projects/Surveillance-Expansion.md) Milestone 5).
`semantic_search` (embedding-based search, not identity recognition) remains
enabled and was not part of that decision.

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
