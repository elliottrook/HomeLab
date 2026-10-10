# V5b corrected accepted-corpus release preflight

Date: 2026-09-26
Status: **READY LOCALLY / NOT AUTHORIZED**

## Frozen artifacts

- Candidate-manifest SHA-256:
  `1222881382e7c5e7c9e33d95078dd2f640bedb69f0260bc663ca09d5242ff2c0`.
- Release-manifest SHA-256:
  `721c377dccca4fef1a685427d85f791559f67686b8bbf533439589f88b3a5d0f`.
- User-data SHA-256:
  `bf7e2a99023eac362883ab2c53ea440948d89782cd0509c0ecd5cce1607f0d55`.
- Payload-manifest SHA-256:
  `dc2a9274ae01c6c56c2216f6ae151f96eecd748103e57dce5638d661879165c0`.
- Candidate size: 208,827 bytes across the manifest, seed sources, nine corpus
  artifacts and four pinned implementation sources.

The generated cloud-config parses as YAML, contains 16 exact write entries and
three lifecycle commands. All candidate and release hashes recompute. Both host
scripts pass `bash -n`. Nine focused V5b tests pass, including static sibling-import
closure, isolated generated-source imports and invented-row comparison. The
available adaptive suite passes 274 tests; `test_full_aster.py` could not load in
this workstation runtime because its existing `httpx` dependency is unavailable.
No dependency was installed for this release preparation.

## Read-only Proxmox observation

At preflight, `/cluster/nextid` returned 123. VMs118–122 were stopped and VM123 was
absent. The V5b ISO, `.part`, staging, release and run paths were absent. The
retained source image is 433,651,712 bytes and its SHA-512 matches the payload.
Observed capacity was 47,749,740 KiB available memory, 659,398,088 KiB on active
`local-lvm`, and 68,205,032 KiB on active `local`, above the frozen gates.

These observations are ephemeral. The creation script repeats every condition and
fails closed before mutation.

## Proposed exact mutation window

If separately approved: stage and hash-verify this exact candidate/release packet;
create the NoCloud ISO; create fresh stopped VM123; validate its exact no-vNIC and
no-agent configuration; boot it once offline; capture at most 4 MiB for at most 300
seconds; stop only VM123 if required; retain it stopped with receipts. No retry.

Excluded: mutation of VMs118–122; network or credential attachment; model, tool or
production-service calls; relabeling or tuning; cleanup or deletion; promotion;
and Git push.
