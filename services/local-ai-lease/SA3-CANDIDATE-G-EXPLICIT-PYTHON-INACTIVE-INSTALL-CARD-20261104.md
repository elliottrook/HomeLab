# SA3 candidate-g explicit-Python inactive install card — 2026-11-04

R6 retained content-free guest exit status 126 with zero stdout and 204 stderr
bytes. The installed host adapter directly executed the root-owned mode-0644
guest Python wrapper. Direct execution of a non-executable regular file is the
deterministic cause of status 126.

Replace only the host candidate-g adapter and matching release manifest:

- adapter `101ce58e…e3c9f` → `e8c8cbcc…597a1b`;
- manifest `1d18a86…d9537` → `7bbfd208…596f0`.

The corrected fixed command keeps the guest wrapper non-executable and inserts
only `/usr/bin/python3 -B` before its exact path. Create root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-explicit-python-r1-20261104`
before replacement. Refuse checkpoint existence, baseline/source/custody drift,
non-ready lease, shared state/lock, failed 34-pin load, command-shape proof or
rollback uncertainty.

This inactive effect makes no booking, model call, guest file change, service
stop or restart. It authorizes no retry, model/backend change, blind review,
route, tool grant or promotion.
