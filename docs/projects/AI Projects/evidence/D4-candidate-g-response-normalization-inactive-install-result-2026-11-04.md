# D4 candidate-g response-normalization inactive install result — 2026-11-04

## Outcome

The deterministic R7 parser correction is installed inactive and independently
validated. Two builds produced identical bundle SHA-256
`0fe2e957f669f6c5db73d81c55e8aef68262188ee43368f5ff9fc221e87c16b1`.
The platform source milestone is Forgejo/GitHub-mirrored commit
`2ce5c3e17e18ec3d1b9e38799ef8f9056e51e969`.

Installed root:root mode-0644 one-link identities are:

- workload registry:
  `49fc9ebfb703437e4735093e5f0ed08a1d29ea2fa966b1cf0294b88c9d88a174`;
- 34-pin release manifest:
  `8717c42c8bb24f33ee24cf176b11457766b88e5a90723142bad28842978d55a2`;
- LXC110 runner:
  `372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352`;
- LXC110 wrapper:
  `1c0240fe7ad1c8f11b22410ecb8938edc6a056007f7f1e578ce0c484ec3c9697`.

The host and LXC110 each retain a root-only mode-0700 checkpoint at
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-response-normalization-r1-20261104`.
All 34 release pins load, the registered workload resolves the corrected runner
pin, realistic bounded llama metadata normalizes to the strict
diagnosis/verification object, and unknown metadata still fails closed.

## Independent postcheck

The lease is exactly ready; Doctor is healthy with zero codes; shared state,
locks and the candidate listener are absent. Dispatcher, Doctor, EPUB and
Proxmox services/timers are healthy; LXC104/110/116 are running; Aster Agent,
accepted 9B/SYCL llama and Speech are active. Core and Lab Hours restart counts
remain zero. No booking, model call, service stop/restart, backend change,
route, tool grant or promotion occurred. Exact staging artifacts were removed;
the recovery checkpoints remain.

## Next gate

One fresh R8 attempt is eligible only after the authoritative reservation
ledger is checked for its complete execution and recovery window and all fresh
runtime gates pass. R3–R7 are spent and cannot be retried.
