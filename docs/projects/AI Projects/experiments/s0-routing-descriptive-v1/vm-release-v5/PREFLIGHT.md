# V5 accepted-corpus release preflight

Date: 2026-09-26  
Status: **READY LOCALLY / NOT AUTHORIZED**

## Frozen artifacts

- Candidate-manifest SHA-256:
  `683944a06b63c1106c308525940409184d46f7b4138864c685c3e118c56c6374`.
- Release-manifest SHA-256:
  `1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.
- User-data SHA-256:
  `3a5f047cd9f729e108169e3d8690005c9fef94865f3739be3e2c4063b58c4519`.
- Payload-manifest SHA-256:
  `4c6abae20160875196a2a94d998f0cba7553199876f1f88b9687d4410c95fd9d`.
- Candidate size: 193,735 bytes across the manifest, seed sources, nine corpus
  artifacts and three pinned implementation sources.

The generated cloud-config parses as YAML and contains 15 exact write entries and
three lifecycle commands. Both host scripts pass `bash -n`. Focused candidate,
worker, release-validator and release-packet tests pass. The full adaptive suite
must pass again immediately before committing this packet.

## Read-only Proxmox observation

At preflight, `/cluster/nextid` returned 122 and VMs118–121 were stopped. VM122,
the V5 ISO, staging, release and run paths were absent. The retained source image is
433,651,712 bytes and its SHA-512 matches the payload. Observed capacity was
48,874,524 KiB available memory, 660,647,421 KiB on active `local-lvm`, and
68,217,404 KiB on active `local`, above the frozen gates.

These observations are ephemeral. The creation script rechecks every condition and
fails closed before mutation.

## Proposed exact mutation window

If separately approved: stage and hash-verify this candidate/release packet; create
the NoCloud ISO; create fresh stopped VM122; validate its exact no-vNIC/no-agent
configuration; boot it once offline; capture at most 4 MiB for at most 300 seconds;
stop only VM122 if required; retain it stopped with receipts. No automatic retry.

Excluded: changes to VMs118–121, network attachment, credentials, models, tools,
production services, relabeling/tuning, cleanup/deletion, promotion and Git push.
