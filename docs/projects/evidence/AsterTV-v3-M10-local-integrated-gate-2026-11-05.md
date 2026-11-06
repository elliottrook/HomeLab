# AsterTV v3 M10 — local integrated gate

Date: 2026-11-05

Status: local half passed; connected M10 gates remain open

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

Two consecutive executions emitted byte-identical JSON with SHA-256
`852eb49ff2e243be51d521fd0b075d94c750609b7d3a6e29d473f02d15b12a61`:

- outcome: `pass-with-connected-gates-open`;
- 49 local test files passed;
- 93 candidate files passed the existing private-key/credential-assignment
  scan;
- immutable v2 release remained
  `e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7`;
- all 15 v3 pages and 127 focus controls passed with zero failures; and
- two M9 candidate builds matched
  `254ac8bdb8b49989e4157d42824e06ed7ced3bd25836e9d8fa412a295345bc16`.

M9 is now part of the normal page candidate source/secret scan and focused
candidate gate, preventing a later release build from omitting it silently.

## Explicitly open connected gates

1. run the Aster Remote/gateway suite in LXC 104's pinned environment;
2. run the connected Jen HEVC decoder test under its existing client-specific
   1080p/stereo policy;
3. prove interrupted install, corrupt package, dependency outage, reboot and
   full v2 rollback on a named canary;
4. collect page/art/network/speech/idle resource evidence;
5. reconcile Doctor, Beszel, backup/restore, NetBox, wiki, reference and mirror;
6. complete a non-author physical walkthrough.

No appliance, service, account, network rule or remote system changed while
building or running this local gate.

