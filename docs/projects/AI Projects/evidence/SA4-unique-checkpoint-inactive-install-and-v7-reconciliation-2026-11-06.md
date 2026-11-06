# SA4 unique-checkpoint install and v7 reconciliation — 2026-11-06

**Result: PASS — v7 reconciled with zero repair effects; v8 installed inert.**

The exact two-file packet was installed create-exclusive in LXC104. The
pre-claim reconciler and v8 runner are root-owned, mode-0644, one-link regular
files at their reviewed hashes. Each rejected an unexpected argument before
reading transaction state.

The reconciler was then invoked exactly once. It accepted only the retained v7
state and wrote root-owned mode-0600 receipt `a0ff3a18…a8c4e`. The receipt
records the deterministic `CHECKPOINT_PATH_COLLISION`, zero checkpoint
creation, zero grant claims, zero repairs and zero observer requests. The v4
ledger remains retained at `ready`/`use_count=0`; it is not reusable. The old
checkpoint and target are byte-identical at `a9831e62…4da0`. Only the exact
plan-bound operation lock and emergency-stop files were released.

After reconciliation, no SA4 process or runtime control remains, the observer
exchange is empty and the whole-host lease is `ready`. LXC104/110/116, Aster
Agent, accepted llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd` are
healthy. No service action, restart, model change, route or promotion occurred.
