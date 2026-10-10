# V1 disposable-VM correction candidate

Date: 2026-09-26
Status: **local review artifact; no ISO, VM creation or boot authorized**

## Evidence-bound correction

The V2 forensic record proves that candidate v0 failed before Python execution:
systemd could not open `/dev/ttyS0` for `StandardOutput=tty` inside the
`PrivateDevices=yes` service namespace. Candidate v1 keeps the private-device
control and moves serial publication outside the sandboxed computation:

1. the unprivileged canary writes `result.json` and the bounded framed stream to
   `protocol.txt` under `/var/lib/aster-s0/output`;
2. the unit writes ordinary diagnostics to the journal and has no TTY directive;
3. only after a successful unit exit, the root-owned cloud-init lifecycle copies
   the protocol file to `/dev/ttyS0`; and
4. the effective oneshot start deadline is tightened from 100 to 90 seconds while
   retaining `RuntimeMaxSec=90` as defense in depth; and
5. the lifecycle syncs and powers off on both success and failure.

This change does not broaden the canary identity, writable paths, address families,
capabilities, model/corpus access or infrastructure authority. Run and NoCloud
instance identities advance from `bootstrap-canary-001` to
`bootstrap-canary-002`.

## Frozen candidate

- Candidate manifest SHA-256:
  `c5e4eb98bc7847e97969b9a853b3da4cf801bcbb5748e53ac2f9c9b6f82831bf`
- Payload manifest SHA-256:
  `56da5b4614220bfc8e51e5b625e8b6bdd87ba30177696a89df6dc66b45fc7f56`
- Pinned Debian image and SHA-512 are unchanged from v0.
- Accepted corpus is absent; evaluation and infrastructure authorization remain
  false in the payload manifest.

## Proposed execution gate

A future approval must name this exact candidate and permit these bounded stages:

1. Re-run host health, capacity, task, current guest-state and free-VMID checks.
2. Verify every candidate file against `candidate-manifest.json`.
3. Create a new `aster-s0-bootstrap-canary-002.iso` from only `user-data` and
   `meta-data`; record listing, size and SHA-256 before attachment.
4. Create a **new** stopped disposable VM from the already pinned source image.
   Do not reuse or mutate VM118's booted disk. The new VM must match
   `vm-config-proposal.json` and contain no vNIC, agent, credential, passthrough or
   shared filesystem.
5. Stop after stopped-state verification. A one-boot V2b canary is a distinct
   execution gate even if both stages are approved together.
6. For one V2b boot, capture at most 4 MiB for at most 300 seconds, send no serial
   input, force-stop only the new VM at deadline, perform no automatic retry and
   parse only the exact `bootstrap-canary-002`/manifest identity.

Success requires one canonical protocol result, only the `lo` interface, a clean
poweroff, unchanged existing guests, and `corpus_evaluated=false`. Anything else is
failed or inconclusive. V3 and accepted-corpus execution remain prohibited.

## Rollback and retention

Before boot, keep the new VM stopped if any gate fails. After boot, stop and retain
the new VM, seed, bounded capture and manifests for review. Deleting VM118, the new
VM, volumes, images, seeds or captures is outside this candidate and requires a
separate destructive-action approval.
