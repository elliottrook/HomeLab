# A1 fixed host-source adapter candidate — 2026-10-18

**Status:** offline, uninstalled and unwired. No live source path was read;
no lease, watchdog, model or production effect occurred.

`application_b60_host_sources.py` adds the next custody boundary for the
pre-lease candidate. A source envelope is accepted only when its fixed path
is non-symlinked, root-owned, mode `0600`, single-link regular file beneath a
root-owned mode-`0700` parent, within the bounded size, and exact-schema JSON.
The adapter also requires the expected source ID, cycle, non-future
observation time, and a payload SHA-256 matching both the envelope and a
caller-pinned expected digest. Only then does it return an `AttestedSource`
with `verified=True`.

Evidence:

- Focused custody/digest tests: 2 passed.
- Complete `scripts/local-ai` suite: 218 passed, 4 expected macOS
  root-custody skips.
- The adapter is not wired into the live entrypoint and cannot authenticate
  synthetic source objects by itself.

Remaining gates are fixed production paths and pinned payload digests for
Proxmox, TrueNAS and LXC observers; target-Linux root proof; source-specific
schema adapters; rollback; measured recovery/lag evidence; and separate host
change and application-only drill approvals.
