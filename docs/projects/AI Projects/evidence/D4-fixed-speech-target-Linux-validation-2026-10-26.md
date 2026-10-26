# D4 fixed Aster Speech boundary — target-Linux validation

**Date:** 2026-10-26  
**Result:** PASS  
**Effect:** isolated temporary staging only

## Bundle tested

The 14,560-byte source/unit archive had SHA-256
`e9724356c67b42fd7720970bef6f65237e9eee18d251e721fc65bf9506578d21`.
It contained the fixed speech catalogue, adapter, response, capability,
gateway, caller, focused tests and two proposed units plus sysusers file.

## LXC104 result

In a new root-only temporary directory:

- the transfer hash matched;
- the focused catalogue/projection/capability/gateway/caller suite passed
  **22/22** under Python 3.13.5;
- all six new Python modules compiled;
- `systemd-sysusers --dry-run` accepted the distinct
  `aster-speech-client` group and `aster-speech-caller` user proposal without
  creating them;
- the exact gateway unit passed `systemd-analyze verify`; and
- the exact caller unit separately passed `systemd-analyze verify` inside
  LXC104, where its broker and interpreter dependencies exist.

The host archive, guest archive, staging directory and temporary caller-unit
copy were all removed. Aster Agent remained active.

## Boundary and next step

No final path, identity, group, socket, unit, daemon state, database row,
grant, live read, model route or model call changed.

The source and unit shape is eligible for a frozen additive bundle manifest.
That manifest must require all new final targets to be absent, retain both
units disabled/inactive after installation, and exclude broker restart,
database enrollment, capability grant and live read. Creating identities and
placing files is a later inactive installation; activation remains separate.
