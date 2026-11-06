# SA4 runtime-control inactive-upgrade review — 2026-11-05

Fresh read-only verification found the installed root owner at
`d8a6d69a…1c39`, the runtime-control owner absent, both runtime control paths
absent and the whole-host lease exactly ready.

The corrected inactive packet performs exactly two file operations on LXC104:

- checkpoint and atomically replace the root owner with `e250bb2c…e3e`;
- exclusively create the runtime-control owner at `6d6e89d2…0daa`.

Rollback restores the exact predecessor and removes only the exact new file,
and stops on uncertainty. Installation does not create the lock or emergency
stop, invoke the owner, create authority, claim a ledger, checkpoint the target
or repair anything.

Packet tests pass 3/3 and the full SA4 suite passes 155/155. This review made
no live change. The exact inactive installation is the next explicit effect
gate; the repair approval that ended in the pre-effect NO-GO is not reused.
