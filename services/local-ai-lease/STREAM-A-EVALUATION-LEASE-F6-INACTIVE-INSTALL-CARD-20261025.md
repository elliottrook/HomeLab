# Stream A F6 watchdog/recovery packet — inactive install card

Status: **SOURCE-ONLY; NOT INSTALLED, ENABLED OR ARMED**

This packet prepares the independent deadline watchdog and owner-heartbeat
boundary for later review. It does not authorize installation, timer enablement,
lease acquisition, consumer stop/start, recovery, model calls, schedule changes,
state creation, or Git push.

## Fixed custody and effect boundary

The future packet uses only these fixed paths:

| Purpose | Path |
|---|---|
| Durable lease | `/var/lib/local-ai-lab/stream-a-evaluation/lease.json` |
| Lease lock | `/var/lib/local-ai-lab/stream-a-evaluation/lease.lock` |
| Operation lock | `/var/lib/local-ai-lab/stream-a-evaluation/lease.operation.lock` |
| Owner heartbeat | `/var/lib/local-ai-lab/stream-a-evaluation/owner-heartbeat.json` |
| Watchdog status | `/var/lib/local-ai-lab/stream-a-evaluation/watchdog-status.json` |
| Restore observation | `/var/lib/local-ai-lab/stream-a-evaluation/restore-observation.json` |
| Restore intent | `/var/lib/local-ai-lab/stream-a-evaluation/restore-intent.json` |
| Identity | `/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json` |

Identity and heartbeat/observation files are root-owned mode `0600`; their
schemas are exact, duplicate-key rejecting, and bound to `lease_id` and
`generation`. Missing owner heartbeat is treated as owner loss and may invoke
only deadline-bound recovery. Foreign, malformed, symlinked, weakly-custodied
or stale identity/state/heartbeat data fails closed without a callback.

The watchdog can call only `run_bound_from_state` and its constrained callback.
The callback writes one root-only restore intent and invokes only the pinned
`stream-a-evaluation-lease --phase restore --state <fixed> --intent <fixed>
--effect-authorized` entrypoint. It cannot acquire a lease, start a workload,
start the backend, or resume an incomplete workload. Callback failure retains
the durable lease, lock and restore intent for reconciliation.

## Pinned packet

The implementation source and all target artifacts must match the final
metadata follow-up. Hashes are recorded after the implementation commit:

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/stream_a_evaluation_watchdog.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_watchdog.py` | 0644 | `REPLACE_AFTER_COMMIT` |
| `scripts/local-ai/stream_a_evaluation_owner_heartbeat.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner_heartbeat.py` | 0644 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-watchdog` | `/usr/local/sbin/stream-a-evaluation-watchdog` | 0755 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-owner-heartbeat` | `/usr/local/sbin/stream-a-evaluation-owner-heartbeat` | 0755 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-watchdog.service` | `/etc/systemd/system/stream-a-evaluation-watchdog.service` | 0644 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-watchdog.timer` | `/etc/systemd/system/stream-a-evaluation-watchdog.timer` | 0644 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-owner-heartbeat.service` | `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.service` | 0644 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-owner-heartbeat.timer` | `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.timer` | 0644 | `REPLACE_AFTER_COMMIT` |

The packet depends on the already pinned entrypoint and four-library packet.
The units must remain disabled and inactive after installation; no identity,
heartbeat, lease, lock, observation, status or restore-intent file is created
by the inactive install.

## Inactive verification

1. Verify the implementation commit, all hashes, root ownership, modes,
   regular-file type, no symlinks, and hierarchy-preserving package layout.
2. Install only the eight listed artifacts, with the two wrappers executable;
   do not create identity or runtime state. Run imports with `-B` and the full
   lease/watchdog test set.
3. Invoke both wrappers without `--effect-authorized`; require the exact
   disabled response and no `__pycache__` or `.pyc` files.
4. Run static unit checks. Confirm both services and timers are disabled and
   inactive, with no lease, lock, heartbeat, status or restore intent.
5. Confirm no production service, F2 timer, GPU holder, backend, endpoint,
   schedule or model request changed.

## F6 activation boundary and rollback

After a separately reviewed F5 post-backup observation, a new approval is
required before creating the root-owned identity and enabling only these two
timers. Activation must checkpoint the exact disabled state, verify the owner
identity/generation, and prove the watchdog can read but not mutate a healthy
lease before any deadline drill. Manual starts remain refused.

On any hash, custody, unit, schema, owner-liveness or static-check mismatch,
disable/stop only these candidate timers, remove only this packet, and verify
the pre-install absence manifest. Never clear historical state, touch F2,
restore production services, or remove the accepted backend. If any state is
uncertain, retain it for manual reconciliation and do not retry automatically.
