# Full-Aster challenger artifact staging card — 2026-10-26

## State

**APPROVAL-READY — source selection and capacity pass; no download has run.**

This card stages one immutable candidate artifact on the Proxmox host. It does
not mount the file into LXC 110, stop or restart a service, load a model, start
a lease or make a model request.

At 19:13 PDT, read-only checks showed:

- `local-ai-lease status`: `ready`;
- Proxmox root available: 59,470,905,344 bytes;
- LXC 110 root available: 21,868,818,432 bytes;
- LXC 110 memory/swap: 16,384/512 MiB;
- LXC 110 running and `aster-llama.service` active/running with zero restarts;
- the accepted model symlink still resolves to the pinned 9B blob.

The 20,419,565,568-byte candidate plus the mandatory 20 GiB remaining-host
floor requires 41,894,402,048 bytes, so host staging fits with about 17.6 GB
additional headroom. Copying into the guest does not meet the same floor and
is prohibited.

## Exact bounded effect

1. Recheck lease-ready, no competing backup/pull/maintenance and at least
   41,894,402,048 host bytes free.
2. Create a new root-owned mode-0700 host directory under
   `/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1`.
3. Download only
   `Qwen3.6-35B-A3B-Q4_K_M.gguf` from maintainer repository
   `ggml-org/Qwen3.6-35B-A3B-GGUF` at exact revision
   `baec3ebee244827cda0f4557eafa8b28f7545fa6` to a `.part` file.
4. Require exactly 20,419,565,568 bytes and SHA-256
   `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`.
5. Atomically rename the verified file and set root:root mode 0400. Record only
   URL revision, file identity, size, digest, times and free space.
6. Recheck lease ready, production service active/running with zero restarts,
   accepted model path unchanged and no new LXC mount.

Abort before the 00:30 backup quiet period. On failure or hash/size mismatch,
remove only the new partial/staging directory after confirming it is not
mounted or open. Preserve an uncertain artifact in place and report it rather
than deleting evidence.

## Explicit exclusions

No guest-root copy, bind mount, unit/configuration change, model load, consumer
stop, service restart, lease, benchmark, private packet access, routing change,
timer change or remote Git write is included. A later read-only mount and
two-request compatibility screen require their own exact effect transaction
after F6 recovery gates permit it.
