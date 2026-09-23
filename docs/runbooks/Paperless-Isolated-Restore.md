# Paperless-ngx isolated restore drill

Prepared and executed 2026-09-21 after Jason explicitly confirmed this bounded drill. Future executions require fresh approval and target checks.

## Verified prerequisites

- Production is LXC 115; never restore over it or change its configuration.
- VMID 915 absent from both `pct list` and `qm list`; recheck before creation.
- Proxmox has approximately 618 GiB available in local-lvm and 45 GiB available RAM.
- Source is the TrueNAS copy exposed through Proxmox's existing read-only NFS mount:
  `/mnt/backup-relay/homelab-proxmox-guests/vzdump-lxc-115-2026_09_21-02_44_54.tar.zst`.
- SHA-256: `8d8ee04aee8fd1f6dbaa09cd9b3f55709af2a344438908c1e3ebbba1e55597b1`.
  Source and TrueNAS copy passed Zstandard integrity checks.
- Embedded config: unprivileged Debian, 2 cores, 2048 MiB RAM, 32 GiB rootfs,
  one NIC, no extra mounts or hooks. Original NIC and onboot settings must
  never be used to start the restored guest.

## Approved scope to request

One temporary restore, offline inspection, network-isolated boot and application
validation, followed by removal of that exact temporary guest and its new disk.
No production change, token issuance, real-document inspection, off-site sync,
firewall modification or new network attachment is included.

## Procedure

1. Recheck ID availability, capacity, read-only mount and archive hash. Stop on drift.
2. Restore without force or automatic start:

   ```sh
   pct restore 915 /mnt/backup-relay/homelab-proxmox-guests/vzdump-lxc-115-2026_09_21-02_44_54.tar.zst --storage local-lvm --hostname paperless-restore-test-915 --onboot 0 --start 0 --unique 1 --net0 name=eth0,ip=manual,ip6=manual,link_down=1
   ```

3. While stopped, explicitly remove the restored NIC:

   ```sh
   pct set 915 --delete net0 --onboot 0
   pct config 915
   pct status 915
   ```

   Require stopped state, onboot=0, no net entries, no host bind mounts,
   devices or hooks, and rootfs belonging to 915. Abort before boot otherwise.
4. `pct mount 915`; inspect the restored compose-file presence and named-volume
   directories without printing environment files or credentials. Locate the
   SQLite database and run `PRAGMA quick_check` with SQLite read-only URI mode.
   Print integrity result only, never document content. Unmount using `pct unmount 915`.
5. `pct start 915`; verify the guest has no external interface/default route.
   Docker bridges inside its isolated namespace are expected. Observe bounded
   startup, container health and HTTP 200 at `http://127.0.0.1:8000/accounts/login/`
   using `pct exec 915`. Do not grant network access to fix an offline failure.
6. Check production 115 still healthy with login HTTP 200.
7. Record results. Stop only 915, recheck its hostname/rootfs identity, then
   `pct destroy 915` to remove the disposable guest and its new disk. Confirm ID
   and disk removed; source archives and production 115 remain intact.

## Recovery and limitations

If any assertion fails, stop the disposable guest and retain its isolated state
for inspection. Never force a restore over an existing ID or delete an ambiguous
volume. Cleanup is confined to resources positively identified as created by
this drill. The original guest and both archive copies are the recovery path.

This proves same-site archive recovery, database integrity and offline application
startup. It does not prove off-site retrieval, OCR/inference behavior or recovery
of changes made after the September 21 02:44 backup (including the reader account).

## Execution result — 2026-09-21

Passed. The TrueNAS archive hash matched through the read-only NFS mount.
Restored to temporary LXC 915 with autostart disabled, removed its NIC while
stopped, and inspected its mounted filesystem. Compose files and the named
SQLite volume were present; read-only `PRAGMA quick_check` returned `ok`.

Booted with no external NIC or default route (only internal Docker bridges).
After normal startup, the restored webserver became healthy and two login
checks returned HTTP 200. No document content or credentials were displayed.
Production LXC 115 remained healthy and returned HTTP 200 throughout validation.

Stopped and re-identified 915, then destroyed it. Confirmed both its configuration
and `vm-915-disk-0` were removed; both original archive copies remained present.
No rollback was needed. Off-site recovery and changes after the archive timestamp
remain outside this evidence.

## Post-deployment repeat — 2026-09-23

The full close-out authorization covered this repeat. The new archive
`vzdump-lxc-115-2026_09_23-12_24_24.tar.zst` and its TrueNAS copy share SHA-256
`a31c8fcf50fe6218f8826848ae2aad8e6726f0cf76f4ea1398fab98394061a88`.
The source passed full Zstandard validation. Restored from the TrueNAS read-only
mount into fresh 915, removed net0 while stopped, and inspected both Paperless
and derived-state SQLite databases: integrity `ok`. The inference key remained
0600, all-mode config and enabled timer were present, and release files matched
the exact export manifest. Booted with no external NIC/default route; broker and
timer were active, webserver became healthy, and two login checks returned 200.
Production remained healthy. Stopped, re-identified and removed only guest 915
and its new disk. This archive stays local/TrueNAS under the corrected policy;
offsite recovery covers service code only, not the document collection.
