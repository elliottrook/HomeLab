# Backup and restore contract

The live deployment milestone is blocked until this contract is translated to
the selected storage platform and an isolated restore passes.

## Protected set

1. Stop ROMarr and the broker; prevent new RomM writes.
2. Take a transaction-consistent MariaDB dump and record its checksum.
3. Snapshot/export RomM config, resources, assets (including saves/states),
   ROMarr config, broker SQLite state, and the non-secret deployment manifest.
4. Export secret references and recovery instructions, never secret values.
5. Record exact image digests and schema/application versions.

Valkey is reconstructible cache/queue state and is not the authority for user
data. Download staging is disposable. ROM files are large media covered by
storage snapshots and integrity manifests, not by the app-state backup.

## Required isolated restore proof

- Restore under a new private hostname with acquisition and all outbound
  downloads disabled.
- Restore MariaDB before RomM, then RomM state, ROMarr state, and broker state.
- Confirm account/catalog counts, save/state counts, proposal counts, and a
  sampled ROM checksum without recording game titles in the evidence.
- Confirm ROMarr cannot overwrite an existing canonical file and can restore a
  quarantined synthetic fixture.
- Run the content-silent Doctor probe and record duration and checksums.
- Destroy the disposable restore only after evidence is retained.

