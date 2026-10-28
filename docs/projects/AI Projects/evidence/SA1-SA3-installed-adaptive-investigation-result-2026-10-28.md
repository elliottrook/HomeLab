# SA1–SA3 installed adaptive investigation result — 2026-10-28

## Result

**PASS for the currently registered three-observation class.** The installed
SA1–SA3 path completed one isolated, connected investigation using the current
sanitized Doctor report and the accepted `qwen3.5-9b` service. It selected and
executed only the two remaining registered read-only observations, then issued
a no-authority completion from the resulting evidence.

This is a daytime main-project result. It did not use the lab-hours F2/F3
chain, change a model, restart a service, or rely on the full-Aster candidate.

## Exact sequence

1. The fixed Doctor reader supplied one `homelab-doctor/status` observation.
   Its bounded state was `fail`; report names and content were not emitted.
2. Model decision 1 proposed `aster-gateway/status` with `authority=none` and
   `effect=none`. The fixed gateway producer returned `ok` and atomically
   consumed only that exact pending decision.
3. Model decision 2 proposed `inference-server/status` with `authority=none`
   and `effect=none`. The fixed health producer returned `ok` and atomically
   consumed only that exact pending decision.
4. Model decision 3 returned `complete`, with null target/kind,
   `authority=none` and `effect=none`.

The final bounded counters were three decisions, two consumed observation
decisions and three observations. The exact target order was
`homelab-doctor`, `aster-gateway`, `inference-server`.

## Controls and postchecks

- The reusable loop and its gateway/producer dependencies pass **24/24**
  focused local tests.
- The first host launch failed before a model call because a temporary helper
  filename used hyphens instead of its importable underscore module name. Its
  trap removed all temporary state. The corrected exact runner SHA-256 was
  `65bcb3737b2e49264ffc9859289c7b8a71a3764305050128e8ea205aabe30720`.
- Synthetic incident state lived only in a temporary mode-`0700` directory and
  was removed after the terminal result.
- Aster Agent remained active on PID `26953` with restart count `0`; its
  `/health` response remained exact.
- The accepted llama.cpp/SYCL service remained active on PID `61089` with
  restart count `0` and was idle/healthy after the last proposal.
- The local AI lease returned exactly `ready`.

## Meaning and remaining gate

The installed path now proves a useful bounded adaptive loop for one live
Doctor-led diagnostic class. It does not prove representative breadth across
Forgejo, backup, network, log or configuration incidents. No repair,
automatic routing or generic shell authority follows. The next main-project
step is to add and independently validate another fixed sanitized evidence
source before considering this milestone broadly complete.
