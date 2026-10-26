# D4 candidate-H inactive staging attempt 2 — 2026-10-25

**Result:** PASS; inactive target custody validated

The corrected staging archive had SHA-256
`e4f61d35788c1070b442dec89097e45aa59dfeb5a35e54af20c5239fd19c0ce4`.
The bounded installer had SHA-256
`76ab5f1b5b67b20babfda104d4bb82a9443b96befd71af167ac74ca8611e1adf`.
Both hashes matched on Proxmox and in LXC104. The target-side bundle validator
reported the exact inactive candidate, eleven packet files, three persistent
control files and one temporary validator.

The corrected content-free validator returned status `pass`, UID/GID 977,
zero supplementary groups, eleven readable but immutable packet files, denied
credential-file access, successful fictional descriptor delivery, no API-key
environment entry, an empty private output directory, credential read `false`,
model calls `0`, and candidate unit state `inactive`/`static`.

Independent postcheck matched every packet SHA-256 to the frozen manifest.
Custody is root:aster-d4-eval 0750 for the source directory, root:aster-d4-eval
0640 for its eleven files, and aster-d4-eval:aster-d4-eval 0700 for the empty
output directory. The launcher, unit and sysusers fragment respectively match:

- `71c07060a59a81923803fdd21cc14f218fc3c1c1f7f1797e1b1e75acdf4240eb`;
- `76c0ba89b26124b1e0fb74e3ddc761a001d937195c4d14ce0c3b5ab0d6b62450`;
  and
- `c4bfc0aa4446d77c252f9cd233842ac101e849ddeddf4347ad30d80298410c64`.

Aster Agent remained active with zero restarts. The accepted llama.cpp/SYCL
service remained active with zero restarts and its actual
`192.168.70.12:11435/health` endpoint returned HTTP 200. The candidate service
was not enabled or started. No journal, model request, credential read, lease,
consumer stop or schedule change occurred.

All temporary staging archives, installers and the target validator were
removed. Only the approved inactive identity, packet, empty output directory,
launcher, unit and sysusers fragment remain.

This completes inactive target custody. It does not authorize a D4 model run.
Candidate-H still needs fresh F2/F3/F4/F5 evidence, executable F6 recovery and
admission, an exact live card and a separate bounded model-call approval.
