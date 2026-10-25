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
| Owner intent | `/var/lib/local-ai-lab/stream-a-evaluation/owner-intent.json` |
| Owner heartbeat | `/var/lib/local-ai-lab/stream-a-evaluation/owner-heartbeat.json` |
| Watchdog status | `/var/lib/local-ai-lab/stream-a-evaluation/watchdog-status.json` |
| Restore intent | `/var/lib/local-ai-lab/stream-a-evaluation/restore-intent.json` |
| Identity | `/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json` |

Identity, owner intent, heartbeat and status files are root-owned mode `0600`;
their schemas are exact, duplicate-key rejecting, and bound to `lease_id` and
`generation`. The persistent `stream-a-evaluation-owner.service` is the only
owner process: it reads the root-only owner intent, records its own PID, boot
ID, process start time, command line and unit identity, and never acquires a
lease. The heartbeat timer can renew only while that exact process identity is
alive. Missing or expired identity-correct heartbeat is owner loss and may
invoke only deadline-bound recovery. Foreign, malformed, symlinked,
weakly-custodied or reused-process identity data fails closed without a
callback.

The watchdog can call only `run_bound_from_state` and its constrained callback.
The callback writes one root-only restore intent and invokes only the pinned
`stream-a-evaluation-lease --phase restore --state <fixed> --intent <fixed>
--effect-authorized` entrypoint. It cannot acquire a lease, start a workload,
start the backend, or resume an incomplete workload. Callback failure retains
the durable lease, lock and restore intent for reconciliation.

## Pinned packet

The implementation source and all target artifacts must match implementation
commit `2360218042ff3bccc7a2ae2dc12642fd69bcdbbb` and its metadata follow-up:

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/stream_a_evaluation_watchdog.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_watchdog.py` | 0644 | `594f833dce9002519940cd2d5361d1d1f81c9303af0103354013efd1af9a0f12` |
| `scripts/local-ai/stream_a_evaluation_owner.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner.py` | 0644 | `REPLACE_AFTER_COMMIT` |
| `scripts/local-ai/stream_a_evaluation_owner_heartbeat.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner_heartbeat.py` | 0644 | `4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc` |
| `scripts/local-ai/stream_a_evaluation_restore_observer.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py` | 0644 | `477aa6a29ec503c39be9896fb04c47f0b2cffa591778c0840edcd84714bfdadb` |
| `services/local-ai-lease/stream-a-evaluation-watchdog` | `/usr/local/sbin/stream-a-evaluation-watchdog` | 0755 | `65012c196134242a76a2131fbc9d7f28b50bcfd9137a87cfda0a416345430c99` |
| `services/local-ai-lease/stream-a-evaluation-owner-heartbeat` | `/usr/local/sbin/stream-a-evaluation-owner-heartbeat` | 0755 | `e0162f60983601192c5f0fdd6d8395604e6636c05c9653c643d3722872dce12a` |
| `services/local-ai-lease/stream-a-evaluation-restore-observe` | `/usr/local/sbin/stream-a-evaluation-restore-observe` | 0755 | `c2968b587c3ec0761c1b43f6811c884d272023bce3dc5679509d894cfc258259` |
| `services/local-ai-lease/stream-a-evaluation-owner` | `/usr/local/sbin/stream-a-evaluation-owner` | 0755 | `REPLACE_AFTER_COMMIT` |
| `services/local-ai-lease/stream-a-evaluation-watchdog.service` | `/etc/systemd/system/stream-a-evaluation-watchdog.service` | 0644 | `02ff7c4a909228023c1cce8704fd9d3e3395f5101add78a919481cbb4a39d932` |
| `services/local-ai-lease/stream-a-evaluation-watchdog.timer` | `/etc/systemd/system/stream-a-evaluation-watchdog.timer` | 0644 | `7b2170f6f6d5e137fee14464b3081d229f37f36af1e1856cbc3de4ed3de79811` |
| `services/local-ai-lease/stream-a-evaluation-owner-heartbeat.service` | `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.service` | 0644 | `a80ee8eca956a435d443e85035a8b03388eb71fdb565969b6c283fa4c0409514` |
| `services/local-ai-lease/stream-a-evaluation-owner-heartbeat.timer` | `/etc/systemd/system/stream-a-evaluation-owner-heartbeat.timer` | 0644 | `a5840b5b4a5bb56b0a05d6641fdaf1f16ca982c1c137bbb9e29f2d4b4b063192` |
| `services/local-ai-lease/stream-a-evaluation-owner.service` | `/etc/systemd/system/stream-a-evaluation-owner.service` | 0644 | `REPLACE_AFTER_COMMIT` |

The packet depends on the already pinned entrypoint and four-library packet.
The live observer uses only verified existing Linux interfaces: `systemctl
is-active`, the installed production authentication probe, `ss` connection
state for port 11435, and `/dev/dri/renderD128` existence. It emits the exact
lease ID and generation supplied by the watchdog, so its fresh output is
identity-bound rather than a trusted prewritten observation file.
The units must remain disabled and inactive after installation; no identity,
heartbeat, lease, lock, observation, status or restore-intent file is created
by the inactive install.

## Inactive verification

1. Verify the implementation commit, all hashes, root ownership, modes,
   regular-file type, no symlinks, and hierarchy-preserving package layout.
2. Install only the twelve listed artifacts, with the four wrappers executable;
   do not create identity or runtime state. Run imports with `-B` and the full
   lease/watchdog test set.
3. Invoke both wrappers without `--effect-authorized`; require the exact
   disabled response and no `__pycache__` or `.pyc` files.
4. Run static unit checks. Confirm the owner, watchdog and heartbeat services
   and timers are disabled and inactive, with no lease, lock, identity,
   heartbeat, status or restore intent.
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
