# M3 35B joined-path correction install result — 2026-10-29

## Result

**PASS — installed inactive from platform commit `309ce983`.** The spent
19:15 booking was not retried or rescheduled. Five files were replaced with
their exact corrected bytes, and all predecessors are retained in the
root-only checkpoint `/var/lib/local-ai-lab/checkpoints/m3-joined-309ce983`.

## Validation

- the installed runtime, runner, registry, transaction and release-manifest
  SHA-256 values match the committed candidate;
- the exact workload resolves through registry and admission with a shared
  2,700-second transaction/preflight/guardian deadline and a 3,600-second
  minimum booking plus 900-second recovery reserve;
- 31 focused joined-path tests and 30 Lab Hours discovery tests pass;
- all 32 installed release-manifest pins match;
- Lab Hours Doctor completed with `Result=success` and exit zero;
- dispatcher, Proxmox daemons, Aster Agent, accepted 9B/SYCL and Speech are
  active;
- lease, operation lock, drain state and drain lock are absent;
- no candidate mount, 35B listener or transaction process remains.

No booking, service stop, guest restart, mount, model call, retry, threshold
change or routing promotion occurred during installation.
