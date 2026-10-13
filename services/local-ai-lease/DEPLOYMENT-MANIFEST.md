# Local AI lease adapter candidate

Status: offline candidate; not deployed or enabled.

Candidate payload:

- `scripts/local-ai/admission_state.py`
- `scripts/local-ai/lease_contract.py`
- `scripts/local-ai/lease_watchdog.py`
- `scripts/local-ai/lease_controller_candidate.py`
- `services/local-ai-lease/local-ai-lease-watchdog.service`
- `services/local-ai-lease/local-ai-lease-watchdog.timer`

The adapter writes a mode-0600 admission record before stopping any guest,
creates one host lock, and uses an explicit allowlist limited to LXC 104, 110
and 116 service units. A failed stop sequence restores only the services it
was allowed to touch. The watchdog remains fail-closed on expiry, heartbeat
loss, partial restoration, GPU loss or schedule drift.

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
the three production services and exact backup schedule are healthy.
