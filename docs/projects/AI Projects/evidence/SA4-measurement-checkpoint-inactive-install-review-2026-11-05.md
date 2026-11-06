# SA4 measurement/checkpoint inactive install review — 2026-11-05

Fresh LXC 104 reads matched the exact older installed measurement-owner SHA
`aa6ebfb2…e70f` and checkpoint-owner SHA `fe8f6385…c45f`.

The source-only packet replaces only those two root-owned mode-0644 files after
retaining exact mode-0600 rollback copies under root-owned mode-0700 checkpoint
`/var/lib/aster/sa4/source-checkpoints/measurement-owner-v1`. Replacement
hashes are `16644ee6…e5e2e` and `b0d8dff3…07614`.

Postchecks require exact metadata, isolated imports with `LOCAL_HOST_ID` equal
to `lxc104`, and one read-only no-follow measurement of the existing canary
against the exact plan precondition. The checkpoint owner is not invoked.
Signing, claims, receipts, target writes, repair, services, timers and routing
are excluded. Any failed or uncertain postcheck atomically restores both old
files and retains evidence.

Two focused packet tests and the complete SA4 suite pass; the suite is
**99/99**. No target file changed. The packet is ready for its bounded inactive
installation and read-only proof.

