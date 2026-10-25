# Stream A exercise runner guest-path repair — inactive card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

The first approved live exercise attempt failed closed before creating any
lease, state or receipt because the runner checked LXC110 helper paths as if
they were Proxmox-host paths. This card replaces only the runner so guest
helper/wrapper custody is checked through `pct exec 110`; it authorizes no
retry, live exercise, consumer mutation, model call, timer change or push.

## Exact one-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/stream_a_evaluation_prepare_only_exercise.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_prepare_only_exercise.py` | `610b963bccacc028401e6656df071e86dfa8c4066028b3e46291d5f3c9e2ec8a` | `cdac8693c41fe1eb47cb0be626da46db2bc51bf4b91478e80b64eae6961b7ab1` | 0644 |

Source commit: `53ad8c20`.

The correction moves LXC110 helper and wrapper pins into explicit
`GUEST_PINNED_FILES`, validates regular/no-symlink/UID/mode/hash inside the
guest, and records guest-qualified pins in the eventual receipt. Host-side
runner, owner, watchdog, observer and F2 checks remain unchanged.

## Required inactive sequence

1. Capture root-owned checkpoint of the exact existing runner hash, mode,
   owner, regular-file/no-symlink property and containing directory. Refuse on
   drift.
2. Replace only the runner atomically, retaining root custody and mode `0644`.
   Do not add/remove state, identity, heartbeat, lock, receipt, unit or timer
   files.
3. Run the complete focused source suite with Python `-B`; require 82/82,
   including the guest-path custody regression and failed-prestate fail-closed
   behavior. Run imports, static hash/mode checks and inert runner validation.
4. Confirm all F6 units/timers remain disabled/inactive, runtime/receipt paths
   remain absent, four consumers remain enabled+active, and October 26 F2
   timers remain unchanged. Do not retry the consumed live approval.

## Failed attempt record

The prior live attempt returned `FileNotFoundError` before any lease/state/
receipt/identity. Postcheck confirmed F6 disabled/inactive, all four consumers
enabled+active, F2 unchanged and whole-host lease ready. That approval is
consumed; a future retry requires separate approval after this repair is
installed and independently verified.

## Rollback

On any failure, restore only the checkpointed runner atomically and rehash it.
Preserve all other packets and runtime custody. If state is uncertain, retain
evidence and stop for manual reconciliation; never retry automatically.
