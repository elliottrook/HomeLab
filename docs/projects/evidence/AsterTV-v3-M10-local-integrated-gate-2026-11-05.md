# AsterTV v3 M10 — local integrated gate

Date: 2026-11-05

Status: local half passed; gateway environment passed; other connected M10 gates remain open

## Gate

`services/kodi/astertv-v3/m10/validate_local.py` discovers every recursively
named AsterTV v3 test plus the design-authority and fleet test suites. It runs
all locally valid files in isolated bytecode custody, scans the complete page
candidate source set for credential assignments/private keys, verifies the
immutable v2 release hash, runs the page-conformance audit and double-builds
the page-aware screensaver candidate.

The only test excluded from local execution is declared by exact path and
reason: `low-spec/test_hevc_decode.py` requires AsterTV-Jen, its retained HEVC
fixture, an idle player and local JSON-RPC. A missing/renamed exclusion fails
closed instead of silently shrinking the inventory.

## Result

After the operations-readiness audit was added, two consecutive clean-tree
executions at commit `746ade8f47fd8454c4926aec0d0f41a48de9e5b7`
emitted byte-identical JSON
with SHA-256
`8c2996f2c9ac570172a291ba7e8d574cf7b86f8e48e2fed9aebe16bb852fe901`:

- outcome: `pass-with-connected-gates-open`;
- 51 local test files passed;
- 93 candidate files passed the existing private-key/credential-assignment
  scan;
- immutable v2 release remained
  `e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`;
- all 15 v3 pages and 127 focus controls passed with zero failures; and
- two M9 candidate builds matched
  `254ac8bdb8b49989e4157d42824e06ed7ced3bd25836e9d8fa412a295345bc16`;
  and
- the operational-readiness projection remained fail-closed at `attention`.
  The clean-tree hash recorded its initial 13 named gaps; Jen's later read-only
  payload refresh reduced the current snapshot to 12.

M9 is now part of the normal page candidate source/secret scan and focused
candidate gate, preventing a later release build from omitting it silently.

## Explicitly open connected gates

1. run the connected Jen HEVC decoder test under its existing client-specific
   1080p/stereo policy;
2. prove interrupted install, corrupt package, dependency outage, reboot and
   full v2 rollback on a named canary;
3. collect page/art/network/speech/idle resource evidence;
4. reconcile Doctor, Beszel, backup/restore, NetBox, wiki, reference and mirror;
5. complete a non-author physical walkthrough.

The former gateway item passed under the separately authorized SA-M10-C1
envelope. See
`docs/projects/evidence/AsterTV-v3-M10-gateway-environment-2026-11-05.md`.
The operations item now has a deterministic gap audit and evidence at
`docs/projects/evidence/AsterTV-v3-M10-operations-readiness-2026-11-05.md`;
it remains open until those gaps are actually closed.

Jen's read-only 124-payload refresh then closed its observation drift. Two
clean-tree runs at `15b662f8c8ff2e726638ebc45bd524ef38de2b47` emitted
byte-identical JSON SHA-256
`7da2a11199ba02b8403f3f1a5b8b6a6a1183d4d9d270d5e4dbef7fa3e62c80d5`,
with 51 passing test files and 12 remaining operational gaps.

Bedroom's transaction-scoped NetBox reconciliation added one bounded local
test and closed one more operations gap. Two clean-tree runs at
`24da9d2df1ac6e6310027164e093c8da69fa4c2a` emitted byte-identical JSON
SHA-256 `b93db1b2a103dc51a3ed8e3b9ee4a04d6aaafa5e3219c12f436af17cb15f883c`,
with 52 passing test files and 11 remaining operations gaps.

No appliance, service, account, network rule or remote system changed while
building or running this local gate. The separate gateway run staged and then
removed only a transient `/tmp` test bundle; it made no persistent change.

