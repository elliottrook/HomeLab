# SA3 candidate-g response-normalization inactive install result — 2026-11-04

The R7 response-envelope correction was installed inactive from deterministic
bundle SHA-256
`0fe2e957f669f6c5db73d81c55e8aef68262188ee43368f5ff9fc221e87c16b1`.
Two independent builds were byte-identical.

The exact installed identities are:

- host workload registry:
  `49fc9ebfb703437e4735093e5f0ed08a1d29ea2fa966b1cf0294b88c9d88a174`;
- host 34-pin release manifest:
  `8717c42c8bb24f33ee24cf176b11457766b88e5a90723142bad28842978d55a2`;
- LXC110 runner:
  `372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352`;
- LXC110 wrapper:
  `1c0240fe7ad1c8f11b22410ecb8938edc6a056007f7f1e578ce0c484ec3c9697`.

All four are root:root regular mode-0644 files with one link. Root-only
mode-0700 host and guest checkpoints are retained at
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-response-normalization-r1-20261104`.
The installed registry resolves the corrected runner pin, all 34 manifest pins
load, realistic known llama metadata normalizes to the strict
diagnosis/verification object, and unknown metadata remains fail closed.

Independent postchecks found the lease ready, Doctor healthy with zero codes,
shared state/locks and port-11436 listener absent, dispatcher/Doctor/EPUB and
Proxmox timers/services healthy, LXC104/110/116 running, and Aster Agent,
accepted 9B/SYCL llama and Speech active. Core and Lab Hours restart counts are
zero. No booking, model call, service stop/restart, backend change, route, tool
grant or promotion occurred. Exact transfer and staging artifacts were removed;
both recovery checkpoints remain.

The installed gate is complete. One fresh authoritative ledger-booked attempt
may proceed under its own fixed runtime checks; R3–R7 remain spent.
