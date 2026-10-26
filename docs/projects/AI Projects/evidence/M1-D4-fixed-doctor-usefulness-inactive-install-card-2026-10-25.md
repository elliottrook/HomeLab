# M1/D4 fixed Doctor usefulness inactive install card — 2026-10-25

Status: **COMPLETED — PASS; INSTALLED INACTIVE**

**Source commit:** `abcaa595`

**Deterministic archive:**
`/private/tmp/fixed-doctor-usefulness-v1-a9468009.tar.gz`, 8,018 bytes,
SHA-256
`7c89cd3a46bfbcff52257e35d0473c9954eb7a73f43ec91f5b54b79f7a1f50ea`.

**Transaction:**
`scripts/aster-adaptive/install_fixed_doctor_usefulness_inactive.sh`, SHA-256
`bc9c297002dffdcea8a9f468284b99354a254b4b96fd401922f0e805fdc96d56`.

## Exact bounded change

After a fresh approval, copy the archive, target validator and staging manifest
to Proxmox `/tmp`, verify all three hashes, and run only the pinned transaction.
It will:

1. require a ready lease, running LXC104, active `aster-agent.service`, absent
   target and no usefulness runner process;
2. copy the packet into LXC104 and construct
   `/var/lib/aster/fixed-doctor-usefulness-v1` as root-owned mode `0700`;
3. install exactly eight root-owned mode-`0600` files;
4. run exact opened-byte staging validation, target imports and runner `--help`
   with bytecode disabled;
5. prove no bytecode cache, output, attempt journal or runner process exists;
6. recheck Aster Agent and the ready lease; and
7. remove the temporary host/guest transport files.

The target is currently expected to be absent. Any failure after staging begins
removes only the new temporary/target directory and transport files. There is
no predecessor to restore.

A read-only preflight at 2026-10-25 22:09 PDT confirmed LXC104 running, the
target absent, no runner process, `aster-agent.service` active and the
whole-host lease ready. These observations must be refreshed immediately
before any approved installation.

## Explicit exclusions

This transaction creates no user, unit, timer, output directory, lease, lock,
receipt, route or model request. It does not read a credential, pass
`--execute`, start or restart a service, enable F6, change the October 26 F2/F3
schedule, or grant authority. Installation proves inactive custody only. A
separate platform admission implementation, exact effectful run card and model
call approval remain mandatory.

## Completion

Jason approved this exact inactive installation. The transaction completed at
22:41–22:43 PDT on 2026-10-25 and its independent postcheck passed. See the
[installation result](M1-D4-fixed-doctor-usefulness-inactive-install-result-2026-10-25.md).

