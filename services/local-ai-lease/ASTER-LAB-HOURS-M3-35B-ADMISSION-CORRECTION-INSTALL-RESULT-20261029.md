# M3 35B Lab Hours admission correction install result — 2026-10-29

## Result

**PASS — installed inactive from platform commit `c424d0a2`.** The spent
15:00 booking was not retried or rescheduled. The installation replaced only
`lab_hours_reserved_runner.py` and `lab_hours_release_manifest.json` and kept
their predecessors in the root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/m3-admission-c424d0a2`.

## Exact validation

- installed runner SHA-256:
  `7adc5b508d68854a3fe65a956732f91812aee99a8f674552326df392bfb8b4ff`;
- installed manifest SHA-256:
  `fe47145d2e2ca9268de9cd7f5fac113970319ddd087c12a533c703c8ad96378f`;
- root custody and modes are `root:root 0755` and `root:root 0644`;
- the installed registry resolves the exact M3 workload to
  `m3-joint-semantic-35b`, and that kind is admitted by the installed runner;
- all 32 release-manifest pins match installed bytes;
- 30 focused source tests and 29 Lab Hours discovery tests pass;
- Lab Hours Doctor completed with `Result=success` and exit zero;
- dispatcher, Proxmox daemons, Aster Agent, accepted 9B/SYCL and Speech are
  active;
- lease, operation lock and shared state are absent, and no model mount or 35B
  process remains.

No booking, service stop, guest restart, model mount, model request, threshold
change, retry or route promotion occurred during installation. A future public
gate needs a new conflict-free booking and remains a distinct transaction.
