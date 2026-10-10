# V3b corrected release preflight

Status: **prepared locally; not staged or executed**

Read-only observations on 2026-09-26 found next VMID121, VM120 stopped, VMID121 and
the new seed/ISO paths absent, 48,910,368 KiB available memory, 661,813,465 KiB
available on `local-lvm`, and 68,219,836 KiB on `local`. These are volatile and the
release script rechecks its fail-closed gates immediately before mutation.

The release imports the checksum-pinned original image into fresh VM121, creates a
new ISO from only `user-data` and `meta-data`, and validates the stopped one-core,
1-GiB, 8-GiB, OVMF/serial configuration. It permits no vNIC, agent, share,
passthrough, credentials or automatic start. VMs118–120 must remain stopped.

The one-boot script refuses an existing run path, revalidates VM config and ISO,
captures at most1 MiB for at most300 seconds, applies one deadline stop if needed,
and never retries. Strict local decoding must bind `isolation-fixture-002`, require
all ten checks true and retain all failures.

