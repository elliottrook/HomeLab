# SA4 reversible inactive-install packet — 2026-11-05

## Result

The approved first-target source has been converted into a fixed, source-only
inactive-install plan. The plan cannot execute commands or contact LXC 104. It
contains no transport, service, unit, timer, booking, key material, grant,
checkpoint, repair invocation, restart, model change or route.

The packet names exactly three future directories:

- `/usr/local/libexec/aster-sa4`, root:root mode 0755;
- `/var/lib/aster/sa4`, root:root mode 0700; and
- `/var/lib/aster/sa4/checkpoints`, root:root mode 0700.

It pins 16 SA4 source programs plus the exact drifted canary fixture as 17
root:root mode-0644 payloads. Every payload digest is checked against the
retained repository bytes. The target remains
`/var/lib/aster/sa4/canary-adapter.json`; its fixed drifted identity is
`19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.

Plan generation fails closed unless a fresh no-follow preflight reports the
entire exact directory and file set absent—neither a subset nor a superset is
accepted. This prevents the future installer from overwriting or adopting an
unowned path. The rollback list is the exact reverse payload order followed by
the three empty directories. Rollback is allowed only when the paths were
created by this packet and every file still has its installed digest; any
changed, missing, linked or uncertain object must be retained for
reconciliation.

The focused four-case packet suite passes. The complete SA4 source suite passes
**67/67**. No live path was created or changed; the last fresh live check at
the preceding source milestone found the whole target path set absent. That
absence evidence must be refreshed immediately before any future installation.

## Boundaries

This milestone is design only. It does not authorize or perform the inactive
installation. All three key-custody slots remain empty. It does not authorize
a key, credential access, booking, lease, lock, checkpoint, grant, measurement,
repair, retry, service change or restart.

## Next gate

The next effect is the exact reversible inactive installation on LXC 104. It
requires a fresh all-paths-absent preflight and a separately authorized remote
mutation. After installation, installed hashes, ownership, modes, link counts,
empty checkpoint state, empty key slots and production health must be checked.
Key creation and custody remain a separate credential gate, and the first
repair remains a later exact immediate-approval gate.
