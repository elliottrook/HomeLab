# D4 fixed Doctor response v2 inactive install card — 2026-10-26

## Exact candidate

- source commit: `add484b0`;
- archive: `/private/tmp/fixed-doctor-response-v2-add484b0-complete.tar.gz`;
- archive bytes: `12,193`;
- archive SHA-256:
  `a9f5b31ec4f0ca101a934cde4896b1cd7484f97b30f7b9cddb1da337fe758b1e`;
- manifest SHA-256:
  `fa8dbeb6379b24e6615e8dabe70684185e0d03824026108ff62ae79de9aaf06f`;
- new target:
  `/opt/aster-agent/candidates/fixed-doctor-response-v2-add484b0` in LXC104.

The packet contains nine source/test files plus its manifest. Every file is
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
mtime zero. Its member listing contained exactly seven declared files plus the
manifest and no extended metadata members.

The metadata-free packet then passed member validation but its isolated import
test found two omitted transitive dependencies: `doctor_incident_adapter.py`
and `sysadmin_investigation.py`. The incomplete candidate remained inactive;
the live caller hash, active state and zero restart count were reverified. The
final packet above adds exactly those two repository-pinned dependencies and
now contains ten members including the manifest. The incomplete target must be
removed before extracting the final packet.
