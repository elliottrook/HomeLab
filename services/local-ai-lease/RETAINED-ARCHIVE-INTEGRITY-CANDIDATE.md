# Retained archive integrity candidate

Status: source-only candidate, **not installed, not admission-ready**.

The old full-stop preflight runs serial `zstd -t` after the 03:00 Mac pull. A
43.585 GB LXC110 archive exceeded its 300-second limit. Stream A observed a
successful 367.36-second recheck (possibly cached), with 17.4 and 31.25
seconds for LXC104 and LXC116. The 03:05–03:10 preflight is therefore invalid.

`scripts/local-ai/retained_archive_integrity.py` separates expensive archive
testing from the later lease decision. A fixed Proxmox source scans only the
newest same-day 104/110/116 `tar.zst` artifacts, resolves exact `pvesm` paths,
checks a bounded `zstd -t --quiet`, and binds each success to VMID, volid,
inventory size/creation time, path, device/inode and nanosecond file times.
The completed JSON may be retained in a root-owned 0600 file. At admission,
the verifier re-queries the current fixed inventory and re-stats each exact
file; a stale date, replaced same-path archive, changed metadata, missing
archive, failed/partial check or old receipt fails closed. The resulting
digest is evidence for the existing backup adapter, not a lease grant.

The candidate deliberately does not create a schedule, invoke itself, install
on Proxmox, stop services, activate a watchdog or make a model call. Before a
live card can be considered, the platform owner must:

1. Review source and tests, bind the producer to fixed root-owned host paths
   and an explicit one-time post-backup window; never accept a caller-supplied
   receipt or `integrity_verified` boolean.
2. Measure the October 15 fresh archives in the separate read-only 01:10
   observation and choose a safe budget that avoids the 00:30 backup and
   01:00/02:00/03:00 TrueNAS pulls. The app heartbeat is not a trusted
   producer or hard real-time controller.
3. Integrate the retained digest into the current-cycle Proxmox/TrueNAS
   backup receipt, with fixed task ordering and exact LXC110 mirror checks.
   Do not treat task SUCCESS as archive integrity.
4. Test target-Linux producer → root-custody file → re-stat → lease controller
   state → installed watchdog decode without effects, including changed-file,
   stale-cycle, partial and timeout cases. Check the installed controller,
   not only an uninstalled source candidate.
5. Freeze the new hashes, installation/rollback packet and revised effect
   window. Obtain the separate approval required by the full-stop card before
   enabling a timer or acquiring a lease.

The isolated source suite passed 148 tests with 2 skips on macOS, including
four new retained-integrity tests. This is **offline code evidence** and does
not change the current full-stop NO-GO.
