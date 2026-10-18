# Installed manual helper reconciliation — read-only evidence

Observed from the current Proxmox host on 2026-10-18 via bounded read-only
SSH:

- `/usr/local/sbin/local-ai-lease` SHA-256:
  `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c`;
- owner/mode: `root:root`, `0750`;
- `local-ai-lease status` returned `{"state": "ready"}`;
- the helper defines `ROOT=/var/lib/local-ai-lab` and `LOCK=/var/lib/local-ai-lab/lease.lock`;
- `archive_observation_exclusion()` opens the root directory and takes a
  nonblocking exclusive `flock` before manual acquisition; and
- the helper does not inspect the full-drain candidate marker or
  `full-inference-drain.lock`.

Conclusion: the installed helper and the candidate share an acquisition-time
directory flock, but this does not provide continuous exclusion after the
short-lived candidate CLI exits. Recurring lab hours remain NO-GO until a
persistent supervisor holds the flock or a reviewed legacy-controller change
binds both markers. No host state was changed by this observation.
