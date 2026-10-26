# D4 fixed Doctor response v2 inactive install card — 2026-10-26

## Exact candidate

- source commit: `add484b0`;
- archive: `/private/tmp/fixed-doctor-response-v2-add484b0-clean.tar.gz`;
- archive bytes: `8,405`;
- archive SHA-256:
  `22a3fa0d6b779e1f5f24f7c54155f1ae3cb93e92728ec5a4b4ca7a9f857399f5`;
- manifest SHA-256:
  `f2bc5744041fe17b0937f32247c2fc30618090348103fb6195825b341466859b`;
- new target:
  `/opt/aster-agent/candidates/fixed-doctor-response-v2-add484b0` in LXC104.

The packet contains seven source/test files plus its manifest. Every file is
hash-pinned by the manifest. The directory must be root-owned mode `0700` and
each file root-owned mode `0600`.

## Bounded installation

1. Recheck the target directory is absent and both `aster-agent.service` and
   `aster-fixed-doctor-caller.service` are active with zero restarts.
2. Copy the exact archive to Proxmox temporary custody and then into LXC104.
3. Extract into a new root-only temporary directory, validate every manifest
   hash/name/size, then atomically rename it to the exact target.
4. Run the caller/response tests with the candidate directory first on
   `PYTHONPATH` and use the installed Aster virtual environment.
5. Verify the live caller and Aster service stayed active, their restart counts
   stayed zero, and their installed live source hashes did not change.

Rollback removes only the new candidate directory after confirming no process
uses it. The live source, systemd units, broker database and sockets remain
unchanged.

## Explicit exclusions

This card does not replace `/opt/aster-agent/fixed_doctor_caller.py`, restart or
reload a service, change the broker, call a model, enable routing, grant a tool
or alter any systemd unit. A live cutover requires a separate explicit restart
approval.

## Packaging correction

The first archive was rejected before installation because macOS added
unlisted AppleDouble metadata members. Its temporary extraction and copied
archive were removed, and no target directory or live change remained. The
replacement above was built with Python `tarfile`, fixed root identity and
mtime zero. Its member listing contains exactly the eight manifest-declared
files and no extended metadata members.
