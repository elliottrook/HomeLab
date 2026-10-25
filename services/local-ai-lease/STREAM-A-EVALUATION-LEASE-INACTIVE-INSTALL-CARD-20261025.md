# Stream A evaluation lease inactive-install candidate — rollback/test card

Status: **CANDIDATE ONLY; NOT INSTALLED**

This card packages the smallest target-Linux inactive-install candidate for
independent review. It does not authorize installation or any live effect.

## Pinned candidate

Manifest:
`STREAM-A-EVALUATION-LEASE-INACTIVE-INSTALL-MANIFEST-20261025.json`

The manifest SHA-256 must be recomputed from the clean commit before any future
review or copy operation. It contains only four regular Python sources under
one new destination root:

`/usr/local/libexec/local-ai-lease/stream-a-evaluation/`

All candidate files are root-owned mode `0644`; the destination directory is
root-owned mode `0755`. The candidate has no executable entry point, service,
timer, socket, credential, model, or key path.

## Inactive preflight

Before any future copy, independently verify:

1. the source commit and manifest hash match this card;
2. every source is a regular non-symlink file with the pinned SHA-256;
3. the destination root and all four target paths are absent;
4. no target systemd unit/timer, lease state, operation lock or workload state
   exists; and
5. the current production backend, consumers, schedules and F2 state are
   unchanged.

Any existing destination path is **NO-GO**. The candidate must be copied only
   as inert library files; no import may invoke `main`, no module may be added
   to `PATH`, and no service or timer may be daemon-reloaded or enabled.

## Tests

The independent reviewer must run from the source checkout:

```text
python3 -m unittest discover -s scripts/local-ai -p 'test_evaluation_lease*.py'
PYTHONPYCACHEPREFIX=<temporary-directory> python3 -m py_compile \
  scripts/local-ai/evaluation_lease.py \
  scripts/local-ai/evaluation_lease_adapter.py \
  scripts/local-ai/evaluation_lease_watchdog.py \
  scripts/local-ai/test_evaluation_lease.py \
  scripts/local-ai/test_evaluation_lease_adapter.py
python3 scripts/local-ai/evaluation_lease_watchdog.py --once
git diff --check
```

Expected result is 28/28 tests, successful compilation and diff check, and
`{"effects":"disabled","state":"source-only"}` from the watchdog. No
Proxmox, systemd, GPU, endpoint, consumer or model command is part of this
candidate test.

## Rollback and recovery

Because this is an inactive candidate, the pre-install rollback checkpoint is
the verified absence of the destination root and all four target paths. If a
future copy is approved and any post-copy hash, owner, mode or path check
fails, stop immediately and remove only the newly created candidate root after
confirming it contains exactly the four manifest targets. If target state is
uncertain, retain the root mode `0700` for operator reconciliation and do not
remove or retry it automatically.

No rollback may touch `/usr/local/libexec/local-ai-lease/host_exclusion.py`,
existing lease state, systemd units/timers, F2 state, production services or
any credential. A later effect-adapter deployment requires a separate card,
fresh F2/F3 evidence, target-Linux review and explicit live authorization.

## Explicit non-authorizations

This candidate does not install, arm, acquire or restore a lease; stop or start
any consumer; call the accepted endpoint; run D4 or M3; create a service or
timer; alter F2; read credentials; or push Git.
