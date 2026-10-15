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

A second, bounded read-only check on that same October 14 LXC110 archive at
low I/O priority completed successfully in **367.36 seconds** (exit 0) under
a 900-second cap. Because the first partial attempt may have populated cache,
this is not a cold-read guarantee for the next backup. The previously untested
4,339,284,465-byte LXC116 archive passed in **31.25 seconds** (exit 0) at low
I/O priority. Together with LXC104's 17.4 seconds, the three observed checks
take 416.01 seconds before source-query and path-lookup overhead. Even this
favorable observed total exceeds the five-minute 03:05–03:10 slot.

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

A one-time **01:10 October 15 read-only timing check** is scheduled in this
chat. It may scan only the fresh 104/110/116 archives after the 00:30 backup
and 01:00 TrueNAS pull actually finish, with no host lease and a hard 01:40
stop before the 02:00 pull. It must skip if started after 01:20 or any
prerequisite fails. Its outputs are measurements, **not** the root-owned
source-bound admission receipt or approval for a live drill. The platform
owner must still specify a trusted producer, verify the result and revise the
card and schedule.
