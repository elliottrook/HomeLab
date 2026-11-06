# AsterTV v3 M10 — gateway environment validation

Date: 2026-11-05

Status: passed under authorized SA-M10-C1

## Scope

SA-M10-C1 allowed a deterministic, secret-scanned copy of the Aster Remote
and AsterTV gateway source, static shell and tests to be staged in one uniquely
named `/tmp` directory in Aster LXC 104. It authorized only unit and installer
tests under the existing pinned Python environment plus content-free service
health comparison. It expressly excluded environment-file loading, inference,
media requests, equipment commands, service restart/reconfiguration,
credentials, network policy and every AsterTV client.

## Package controls

`services/kodi/astertv-v3/m10/build_gateway_test_bundle.py` produced a
58,366-byte deterministic archive containing 28 manifest-hashed files:

- archive SHA-256:
  `87e2d21db92511137ea53bd3cadd5828b5632e074e1a34264135a4e509d407dc`;
- `service_mutation: false`;
- `environment_file_loaded: false`; and
- fail-closed rejection of private keys and literal credential assignments.

The only permitted scanner exception is the exact runtime construction in the
named gateway installer; tests prove the same text in another file and split
literal assignments remain rejected. The archive hash matched after transfer,
and all 28 extracted payload hashes matched the manifest before execution.

## Result

Using `/opt/aster-agent/venv/bin/python` without loading
`/etc/aster/aster.env`, all 52 selected Remote, gateway and installer tests
passed in 0.158 seconds. Before and after the run, `aster-agent` remained:

- `ActiveState=active`, `SubState=running`;
- `MainPID=94738`;
- `ExecMainStartTimestampMonotonic=2238719841058`; and
- `NRestarts=0`.

No service restart, configuration write, inference call, media request,
equipment command or client action occurred. The uniquely named LXC staging
directory and Proxmox transfer archive were removed and their absence was
verified. The package is reproducible from committed source.

## Remaining M10 work

The Jen HEVC fixture is absent, so connected decode remains explicitly open.
Recovery/failure rehearsal, resource evidence, operational-system
reconciliation and a non-author physical walkthrough also remain open.
