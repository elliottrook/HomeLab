# Local AI lease adapter candidate

Status: offline advisory candidate; not deployable for live recovery.

Candidate payload:

- `scripts/local-ai/admission_state.py`
- `scripts/local-ai/lease_contract.py`
- `scripts/local-ai/lease_watchdog.py`
- `scripts/local-ai/lease_controller_candidate.py`
- `scripts/local-ai/trusted_observer.py`
- `scripts/local-ai/lease_watchdog_cli.py`
- `services/local-ai-lease/local-ai-lease-watchdog.service`
- `services/local-ai-lease/local-ai-lease-watchdog.timer`

The adapter writes a mode-0600 admission record before stopping any guest only
when test-only effect authority is explicitly injected. Normal construction is
advisory-only and cannot execute commands. It then
creates one host lock, and uses an explicit allowlist limited to LXC 104, 110
and 116 service units. A failed stop sequence restores only the services it
was allowed to touch. The watchdog remains fail-closed on expiry, heartbeat
loss, partial restoration, GPU loss or schedule drift. It does not collect
trusted host observations or execute recovery; those remain open work.

The fixed-probe observer is now available offline. It bounds every probe to
five seconds and checks control-plane/services, GPU visibility, exact model,
binary, unit and auth markers, plus the enabled backup/News schedule set. The
systemd unit is still intentionally refused and requires that observer to be
wired to a root-owned host-observation path. A Mini/chat/network loss cannot
yet recover production because the effect runner remains advisory-only.

## Dry-run procedure

Run the focused controller, watchdog and contract tests from
`scripts/local-ai/` with `PYTHONDONTWRITEBYTECODE=1`. Review the emitted fake
commands and assert that no command occurs outside the allowlist. Do not run
the candidate against Proxmox from a developer checkout.

## Live gate and rollback

Before deployment, capture the current `/usr/local/sbin/local-ai-lease` hash,
unit files, state directory and disabled/enabled timer state. Install the
candidate into a private staging path, run the same fake-command suite, then
request separate authorization for the live host change. If any postcheck
fails, disable the candidate timer, retain the lease lock, restore the saved
controller/unit files, and use the existing manual release path only after
the three production services and exact schedule identities are healthy:
Proxmox `00:30`, TrueNAS guest `01:00`, TrueNAS LXC 110 `02:00`, TrueNAS Mac
`03:00`, and News digest `06:15`/`17:15`, with the expected timers enabled.
