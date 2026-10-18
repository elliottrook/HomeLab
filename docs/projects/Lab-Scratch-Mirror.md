# Disposable lab storage mirror

> Status: Deployed and validated — 2026-10-18. Owner: Jason. Stream M.
> Service/platform: TrueNAS storage V1; lab-only dataset on existing production appliance.
> Platform: TrueNAS 25.10.5; configuration: lab-pool-20261018.

## Purpose and authorization

Jason requested reuse of the two previously rejected SAS disks in a separate
`lab` mirror, accessible to all 192.168.70.0/24 resources. This is disposable
scratch storage for experiments and small media-stack fixtures, never the sole
copy of important data. Existing production pools and new-disk qualification
are excluded. No applications or client mounts were deployed.

## Pre-start risk and recovery

The two unused disks were identified by serial, WWN, capacity and pool absence
immediately before pool creation. Creating the pool erased them as requested.
BK81 has known media defects and prior uncorrected errors; BTVM has a large
non-medium-error history. Mirroring does not make this reliable production
storage. Shared AUTH_SYS access maps all clients to apps:apps (568:568), so all
allowed clients can modify all share content. It is trusted-subnet scratch,
not encrypted or individually authenticated private storage. Firewall access
is restricted to TCP2049; production export restrictions remain unchanged.
No expected service interruption. Abort on unexpected disk identity, occupied
disks, existing lab pool or unexpected production topology changes.

Pre-change pool inventory and SMART baselines are retained at
`/mnt/Media/backup-ops/lab-pool-20261018/`. Firewall checkpoint:
`/conf/backup/config-before-lab-nfs-20261018-155116.xml` (root private).
Rollback: disable NFS share 7 and remove only firewall rule
`3b5a27c1-4caa-4209-b933-3d6b9f29464e`, then reload the filter. Export the lab
pool if retiring it; destruction requires checking for newly stored data.
Do not restore the whole firewall checkpoint over subsequent unrelated edits.

## Implementation and milestones

- M1: Created pool id 3, GUID 17131137145935883182, one two-disk mirror:
  Z1Z0BTVM / WWN 5000c5005611797b and
  Z1Z4BK810000C444B6S9 / WWN 5000c50058c10497.
- M2: Created `lab/shared`, LZ4, atime off, owner apps:apps, mode 0770.
  NFS share id 7 exports `/mnt/lab/shared` read/write to 192.168.70.0/24 only.
- M3: OPNsense opt6 rule sequence 2685 permits this subnet to
  192.168.20.40 TCP2049 before the RFC1918 deny. Filter reload returned OK.
- M4: From LXC114's network namespace (192.168.70.13), an isolated temporary
  NFSv4.2 mount passed 16 MiB random write/fsync/read/SHA256 comparison.
  Ownership was 568:568; test file and mount removed. Guest privileges and
  persistent mounts unchanged. From Proxmox management IP, mount failed with
  NFSv4 `No such file or directory` because the export is not exposed to that
  client (the harness expected `access denied`, so its wording assertion failed;
  the actual mount was correctly refused). Live export table confirms subnet.
- All pools ONLINE/healthy with zero lab ZFS read/write/checksum errors.
  ZFS available space: 3.51 TiB after reservations/overhead.
- New HP disks 37H0A019FT2C1711 and 37H0A01HFT2C1711 remain unused with their
  background long SMART tests in progress. Existing Media/Recovery unaffected.

## Integration and operational handoff

No backups or historical snapshot policy added for disposable lab data.
TrueNAS automatically created its normal scrub task (id 3, Sunday midnight,
35-day threshold). Existing appliance-native/Prometheus/Doctor monitoring
remains the adopted TrueNAS coverage; no Beszel agent added, consistent with
Beszel-NetBox-Coverage-Reconciliation-2026-10-08.md. NetBox API readback confirms
existing TrueNAS device 9 and primary IP record 23, 192.168.20.40/24; no
address, interface or new host changed. Pool/share facts live in this storage
record, not a fabricated new NetBox device. No DNS, Authentik, Homepage,
application release, cloud storage or external endpoint changes required.

Client endpoint: `192.168.20.40:/mnt/lab/shared` using NFSv4 TCP.
For a normal Linux VLAN70 VM, create a mount point then mount with:

```sh
mount -t nfs -o vers=4.2,proto=tcp 192.168.20.40:/mnt/lab/shared /mnt/lab
```

Unprivileged LXCs need a separately planned host-managed/bind mount; Proxmox's
192.168.50.10 address is deliberately not included in the export. Do not change
container privilege or broaden subnet access merely to make a mount work.
No client fstab entries added. Capacity does not imply disk rehabilitation:
replace/recreate scratch storage if faults recur. Local documentation recorded;
Git push remains subject to separate authorization.
