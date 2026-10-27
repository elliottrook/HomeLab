# SA2 first registered producer boundary — 2026-10-26

## Result

**SOURCE-ONLY PASS.** The first connected-evidence candidate consumes only an
already pending SA1 journal decision for the exact pair
`aster-gateway/status`. The authenticated caller supplies no target, producer,
kind, command or path. Every other registered incident pair is denied until it
has its own reviewed producer.

The producer is an in-process gateway self-status check. It has no network,
filesystem, subprocess, credential, model or repair capability. Its strict
producer envelope is validated by the existing incident-store boundary before
the observation is appended and the pending decision is marked consumed.
Repeated execution, a missing decision, a terminal decision, an unregistered
producer pair and an invalid clock all fail closed.

The Doctor incident candidate now preregisters this gateway check after the
existing sanitized Doctor report. The new owner-authenticated `observe` route
can therefore execute one explicitly selected gateway-status follow-up and
return the existing bounded incident snapshot. The legacy API key remains
denied.

## Validation

- dependency-free incident/selector/producer regression: **35/35** with
  `ResourceWarning` fatal;
- LXC104 production-dependency producer and gateway-route suite: **10/10**;
- candidate compilation and `git diff --check`: pass;
- the temporary target packet was removed after testing;
- Aster Agent remained active at PID `17011`, `NRestarts=0`;
- accepted `aster-llama.service` remained active at PID `48161`,
  `NRestarts=0`.

No production source, database, service, route, model or authority changed.

## Remaining boundary

The candidate still requires a frozen release manifest, rollback-capable
installer and one separately approved Aster Agent restart. Broader SA2
producers need individual fixed sources and least-privilege proof; this registry
must not become a generic command or target dispatcher.
