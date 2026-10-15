# Full-stop preflight: measured backup integrity timeout

Status: **current adapter cannot complete the required archive check within
its pinned timeout; live drill NO-GO until redesigned and remeasured**.

On October 14 Vancouver, Stream A used the fixed read-only Proxmox backup
inventory and `pvesm path` to run `zstd -t --quiet` against the latest local
LXC104 and LXC110 archives. The 1,956,833,163-byte LXC104 archive passed in
17.4 seconds. The 43,585,464,294-byte LXC110 archive was still running at
the `FixedSourceAdapters.backup()` per-archive 300-second timeout; Python
terminated that test with `TimeoutExpired`. LXC116 was not tested in this
sequence. No archive was modified and no residual `zstd -t` process was
found. **Timeout does not imply corruption**; it means integrity was not
established by this method in the allotted time.

The proposed 03:05–03:10 preflight and 03:10 full-stop acquisition cannot
complete the current adapter's serial checks on the observed large archive.
This is independent of the [installed controller/watchdog schema mismatch](Full-stop-lease-schema-mismatch-2026-10-14.md).
Do not claim tonight's drill is approval-ready from scheduler SUCCESS alone,
and do not silently increase a timeout or compress the restoration reserve.

A revised card needs a source-bound integrity receipt that is completed before
the lease decision without competing unsafely with the backup chain, or a
measured preflight interval and adjusted cutoff that still protects exact
restoration. The producer must bind the archive identity, size, creation
cycle, check result and capture time; a stale prior archive or a mere file
presence check must fail. Test the accepted LXC110 archive cold, not only from
cache, and retain a failed/unknown outcome if the time budget is exceeded.
