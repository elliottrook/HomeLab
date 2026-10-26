# Stream A candidate-H F6 pure plan review

**Date:** 2026-10-25

**Decision:** pure plan builder **GO**; effect orchestrator remains open

Platform commit `3c18e5a1` adds a pure `stream_a_evaluation_live_plan.py`.
It has no filesystem, subprocess, systemd, network or model effects. It
validates accepted evidence identities, derives fixed lease, owner and
checkpoint identities, constructs the exact entrypoint payload schemas and
fixed intent paths, freezes candidate-H and M3 commands, and enforces call,
elapsed-time, lease-window and 900-second restoration-reserve bounds. Its
combined planner, lease and card suite passes 25/25.

Independent platform review returned **GO** for that pure layer. It found the
schemas, paths, commands, identities and bounds coherent. It also identified
the intentional boundary that must survive implementation: the plan builder
can construct an M3 start payload, so plan construction alone is not admission
or sequencing authority. The future effect orchestrator must submit every
phase through the durable lease adapter, whose state machine admits M3 only
after an accepted candidate-H outcome.

No source is installed and no effect is authorized. The next offline item is
the fixed orchestrator and its synthetic recovery tests; fresh F2–F5 evidence
and a separate live approval remain later gates.
