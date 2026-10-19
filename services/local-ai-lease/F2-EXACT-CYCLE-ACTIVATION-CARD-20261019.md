# F2 exact-cycle activation candidate — 2026-10-20

Status: source-only review candidate. The currently installed daily timers
remain disabled and inactive. This card does not authorize replacement,
daemon-reload, enablement, start, scan, lease, service stop, model request, or
remote push.

## Exact one-shot schedule

Use only these date-specific timer units for the next eligible Vancouver cycle:

| Timer | Exact local elapse | Service | Persistent |
|---|---|---|---|
| `f2-preflight-prepare-20261020.timer` | 2026-10-20 01:09:00 PDT | `f2-preflight-prepare.service` | no |
| `f2-preflight-final-20261020.timer` | 2026-10-20 01:10:00 PDT | `f2-preflight-final.service` | no |

They have no later recurrence. They must be enabled only after a fresh
authorization and only after the existing daily timers are confirmed disabled.
The candidate service files remain the already-installed, verified revision.

## Source hashes

| Source | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261020.timer` | `01c819c23b0b04e415884b44dd34454e28b8dee4aa76bd8dac8c186e4b775449` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261020.timer` | `cd8ac10fd6b0df9b8641ed2bb8961873cf4e65eacbfca92b3145b344e7e55768` |
| `scripts/local-ai/test_f2_exact_cycle_units.py` | `08d2e3107617d57df53b587ed9348419ec3a0a5838b1e26d7523665ec3a4b9f8` |

## Activation plan — not executed

1. Recheck the installed entrypoint, service files, fixed-wrapper pins,
   rollback checkpoint, and absence of any active F2 state or receipt.
2. Stage only the two exact-date timer units as root:root 0644 under
   `/etc/systemd/system/`; run `systemd-analyze verify` and
   `systemd-analyze calendar` against both exact dates.
3. Run `systemctl daemon-reload`, then enable the two exact-date timers only;
   do not start either service or timer manually. Record `systemctl list-timers`
   next and last elapse evidence.
4. After the 01:10 terminal state is `complete` or `no_go`, disable and stop
   both exact-date timers, then verify no F2 timer remains enabled or active.
   If the state is missing, malformed, uncertain, or the final service fails,
   stop and reconcile the timers before any further attempt.
5. Keep the existing daily timers disabled. A future cycle requires a new
   exact-date source card, review, and authorization.

## Post-run observation

Codex heartbeat must observe the state directory, receipt absence/presence,
timer enabled/active state, and the bounded observer result. It must not launch,
retry, extend, acquire a lease, stop services, or compete with the host timers.
It reports only completion, failure, or required user action.
