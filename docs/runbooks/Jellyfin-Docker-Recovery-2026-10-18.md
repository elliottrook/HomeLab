# Jellyfin / TrueNAS Docker recovery — 2026-10-18

## Incident and authorization

Jason reported Jellyfin inaccessible and explicitly approved the proposed
Docker restart. Read-only checks showed Docker active since the morning reboot
but reporting zero containers and zero images. On disk, its configured root
`/mnt/.ix-apps/docker` contained 32 container definitions and 197 image metadata
records. Jellyfin's configuration and media paths were mounted; all ZFS pools
were healthy with ample free space. Port 8096 refused connections.

## Recovery

Ran `systemctl restart docker` at approximately 15:39 PDT. Docker reloaded the
existing container inventory and completed initialization at 15:42:11. No
containers, images, databases or volumes were recreated or restored. No pool,
firewall, proxy, image-version or persistent startup configuration was changed.
Startup involved substantial ZFS reads; transient I/O waits were observed, with
no reported pool errors. Existing restart policies determined which apps started.

Jellyfin finished its own startup at 15:44:36 PDT. Verification:

- `/health` on localhost: HTTP 200, `Healthy`.
- `http://192.168.20.40:8096/web/index.html`: HTTP 200.
- HTTPS `jellyfin-sso.elliottrook.com/web/index.html` through NPM on LXC107:
  HTTP 200, certificate validation enabled, using a local DNS override to reach
  the proxy. This verifies the proxy route, not public DNS or remote-user access.
- All ZFS pools remained healthy. No authenticated playback test performed.
- ARR health checks recovered; Seerr was still initializing at the initial
  Jellyfin handoff. Audiobookshelf/portal/LazyLibrarian shadow containers with
  restart policy `no` remained stopped; no unrelated stack was force-started.

## Cause and follow-up

The empty in-memory Docker inventory despite intact on-disk metadata was
resolved by restarting Docker. A boot-time application-storage mount/order race
is a hypothesis, not a proven root cause. Do not claim that recurrence has been
prevented. Investigate boot ordering and mount visibility before introducing a
permanent startup override. If repeated, first verify the configured Docker root,
mounted datasets, persisted definitions and existing processes; never initialize
an empty replacement application environment over these files.

No destructive rollback is appropriate: recovery used the existing daemon and
container configuration. Documented locally; no Git push authorized by this fix.

## Root cause established in follow-up

The custom `unified-media-portal-firewall.service` was enabled under
`multi-user.target` and declared `Requires=docker.service`. This pulled Docker
into boot independently of TrueNAS's application initialization. Both Docker
and its socket are otherwise disabled for ordinary systemd boot activation.
TrueNAS 25.10.5's installed middleware explicitly mounts `Media/ix-apps`
recursively before starting Docker on the `system.ready` event; those datasets
have `canmount=noauto`, so importing Media alone does not make them available.

A private mount namespace with a read-only, non-recursive bind of `/mnt`
revealed the underlying boot-filesystem `.ix-apps/docker` directory. Its empty
`containers` directory and image/network/buildkit directories were created at
08:42:04, exactly when the prematurely started daemon initialized. The actual
mounted dataset contains 32 definitions. This establishes the empty-root boot
race rather than missing/deleted container data. The temporary inspection mount
was removed; nothing was deleted from either filesystem.

Prepared local correction in
`services/unified-media/unified-media-portal-firewall.service`:
replace `Requires=docker.service` with `PartOf=docker.service`, retain
`After=docker.service`, and change installation to `WantedBy=docker.service`.
Deployment must remove the old multi-user enablement link and enable the revised
unit under Docker, then daemon-reload. Preserve the firewall command unchanged.
This makes Docker pull in its firewall helper, not the reverse, and propagates
Docker restarts to the helper. No Docker restart or NAS reboot is needed just
to install this correction. Verify dependency links and existing firewall rule;
the next planned reboot provides end-to-end boot validation.

Seerr subsequently recovered to healthy during follow-up inspection.

## Approved correction deployed — 15:50 PDT

Jason explicitly approved installation. Saved the original unit under
`/mnt/Media/backup-ops/docker-startup-fix-20261018-155030/`, disabled its old
multi-user enablement, installed the revised unit, reloaded systemd and enabled
it under `docker.service.wants`. The old multi-user link is absent. Docker now
wants the firewall helper; the helper no longer requires Docker and has
`PartOf=docker.service` with `After=docker.service`.

Docker remained active with the same PID (447749); neither Docker nor the NAS
was restarted. The existing NPM-only firewall rule remained present. Jellyfin
returned HTTP 200/Healthy, its HTTPS proxy page returned 200, and Seerr was
healthy. Full reboot validation is deferred to the next planned reboot.

Recovery checkpoint is available for comparison. Do not blindly restore the
old unit's boot enablement: that would reintroduce the confirmed startup race.
