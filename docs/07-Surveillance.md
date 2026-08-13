# Surveillance

**Status:** Operational pilot  
**Last updated:** 2026-08-11

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

Expected results are an NFSv4 source from `192.168.1.40`, an active systemd
unit, a healthy Frigate container and recent MP4 recording segments.

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
