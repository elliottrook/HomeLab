# V3 release preflight

Status: **prepared locally; not staged or executed**.

Fresh read-only observations on 2026-09-26 found cluster `nextid` 120 and VMs 118
and 119 stopped. Those facts are volatile and must be rechecked by the fail-closed
release script immediately before any mutation.

The release creates a new ISO and stopped VM120 from the checksum-pinned retained
Debian image. It does not reuse VM119's booted disk. VM120 has one core, fixed 1 GiB
RAM, 8 GiB non-backed-up OS storage, OVMF, serial console, no vNIC, no guest agent,
no shared directory, no passthrough device, no credentials, and `onboot=0`.

Preconditions include at least 8 GiB host available memory, 16 GiB free on
`local-lvm`, 2 GiB free on `local`, an unused VMID120, absent ISO/release/run paths,
stopped VMs 118/119, exact source/candidate hashes, and exact candidate ISO contents.
Any mismatch stops before boot. Creation ends with VM120 stopped and strict config
validation; boot is a separate command and approval boundary.

The one-run script refuses an existing run directory, revalidates VM config and ISO,
captures at most 1 MiB for at most 300 seconds, forces one stop only if the guest did
not power itself off, and never retries. Strict local decoding and evidence retention
follow capture; the host script itself does not assert that a syntactically complete
capture is semantically successful.
