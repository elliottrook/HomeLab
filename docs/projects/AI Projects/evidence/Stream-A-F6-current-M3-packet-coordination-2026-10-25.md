# Stream A F6 current M3 packet coordination — 2026-10-25

> State: final inactive M3 packet installed and independently verified
>
> Purpose: exact input for the platform-owned current-packet F6 card

The host/V3 composition identities remain recorded in the
[22:48 installed snapshot](Stream-A-F6-current-installed-packet-snapshot-2026-10-25.md).
The M3 paragraph in that snapshot is superseded by this receipt.

## Current LXC110 packet

- runner SHA-256:
  `88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0`;
- scorer SHA-256:
  `7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd`;
- journal validator SHA-256:
  `966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb`;
- complete eleven-file packet-manifest SHA-256:
  `7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80`;
- validated byte total: `99,805`;
- custody: exactly eleven root:root mode-`0600` regular files in the existing
  root-owned mode-`0700` directory; and
- validation: 119/119 dependency-free source tests, 17/17 runner replacement
  tests and 9/9 final target-Linux scorer tests.

The manifest identity is a digest of the reviewed repository fixture. There is
deliberately no installed manifest path inside the eleven-file packet. The F6
card must bind the digest and exact validated file set without inventing one.

`run.json`, `attempt-journal.jsonl`, `__pycache__` and an NLU runner process
were absent after installation. The accepted llama service remained active
with zero restarts and the lease remained `ready`. No model request occurred.

## Card consequence

The platform current-packet activation/recovery card must supersede every
earlier M3 identity, retain candidate-H then M3 as the only admitted serial
sequence, and use the installed V3 composition snapshot plus the identities
above. It must retain the 90-minute bound, protected restoration reserve,
owner/watchdog recovery, no-retry rule and independent terminal postcheck.

The October 26 path is already separately scheduled: F2 prepare 01:15, F2
read-only scan 01:20, reconciliation 01:42 and conditional F3 conversion
01:50. F4/F5 must still be produced fresh from an accepted same cycle before
F6 can be armed. This receipt is coordination evidence only; it grants no
lease, consumer stop, model call, workload, routing action or deployment.
