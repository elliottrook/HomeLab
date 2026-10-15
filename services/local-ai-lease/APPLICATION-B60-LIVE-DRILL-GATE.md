# Application B60 live-drill gate

Status: BLOCKED pending a source-bound pre-lease producer. The disabled helper
upgrade does not authorize this gate.

The current `application_b60_drill` entrypoint rejects arbitrary paths and
requires `/var/lib/local-ai-lab/application-b60/prelease.json`, but that file
must be produced by a trusted root-owned producer. A root-created JSON file is
not evidence. Until this producer exists and passes the checks below,
`acquire` must not be run.

## Required producer inputs

The producer must execute these fixed read-only sources itself, using the
current Vancouver cycle and the lease's proposed ID/generation:

- Proxmox backup artifact metadata and archive checks through the fixed
  `FixedSourceAdapters.backup` path (`backup_receipt_adapter.py` hash
  `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f`; fixed
  source adapter hash `64daf43291eec808e122c1e0fe844e614327049a907d36817fdbaacc46ac73e0`).
- TrueNAS task 1/3/2 completion and the LXC110 mirror, over the pinned
  `aster-schedule-observer` transport and host key.
- A current task-2 Mac exact-subset receipt with claim
  `source-destination-exact-subset`, fixed manifest digest, equal source and
  destination manifests/counts/bytes, snapshots bracketing task 2, and a
  bounded capture. The existing tree-presence summary is insufficient.
- Two fixed consumer/quiescence samples showing only LXC104 Agent and LXC116
  Speech will be stopped by the application lease, while LXC110 remains active
  and News is quiesced. The observer source is `trusted_observer.py`, hash
  `fdc64fc200b87d0faba64a02762df3197fc49366dd0bec12b491ed83fb1aa93f`.
- Exact accepted backend identity, schedule points, GPU, model, binary, unit,
  authentication and service state from the trusted observer.

The producer must write the fixed prelease path atomically, root-owned mode
0600, inside the root-owned mode-0700 application state directory. Its schema
must include the source receipt digests, current-cycle timestamps, lease ID and
generation, and the exact validated `ApplicationPreLease` fields. It must not
accept those source values from CLI arguments or a caller JSON object.

## Required negative tests

Before live approval, tests must reject a fabricated root JSON, stale backup
receipt, missing TrueNAS mirror, tree-presence-only Mac receipt, mismatched
source/destination subset manifests, future capture, partial consumer set,
News still active, wrong lease identity/generation, and a restore window that
misses the 15-minute reserve or 04:15 Vancouver cutoff.

## Later live sequence

1. Run the producer and inspect only its content-free receipt.
2. Run `/usr/local/sbin/application-b60-drill --phase acquire` using the fixed
   producer path.
3. Journal key and ingress intent/observed transitions, start and observe the
   sidecar, then run `--phase admit` using the fixed sidecar observer receipt.
4. Enable only the heartbeat and recovery timers for the bounded lease.
5. Run the separately approved A1 batch through the restricted admission
   transport. On expiry, uncertainty or failed postcheck, retain the lock and
   do not replay effects.
6. Disable both timers, remove the test key, restore ingress, recover consumers,
   and verify the exact production runtime/schedule receipt before release.

No step above is authorized by this gate document. It is a source and review
checklist for the later effectful approval.
