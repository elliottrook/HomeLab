# M3 NLU calibration inactive staging card — 2026-10-25

> State: **READY FOR ONE BOUNDED PRIVATE-DATA STAGING APPROVAL**
>
> Effect: copy the corrected, sealed eleven-file packet into LXC110; do not start a
> lease, process, model request, score, threshold selection or route.

## Why this can happen before lab hours

The current run card unnecessarily orders lease acquisition before copying the
packet. File staging neither uses the GPU nor changes the accepted llama
service. Separating it from execution shortens the later exclusive window and
does not weaken the run gate: a fresh compatible lease, idle endpoint, runtime
pins and restoration reserve are still mandatory immediately before the first
model request.

The 11:27 PDT read-only preflight found:

- `/var/lib/aster-nlu-calibration` absent in LXC110;
- `aster-llama.service` active;
- `/etc/aster-llama-api-keys` mode `0600`, owner `ollama:ollama`, without
  reading its contents;
- 21,457,116 KiB available under `/var/lib`; and
- the host lease controller in `ready` state with no active lease.

## Exact source and destination

Use the eleven entries and digests in
`scripts/aster-adaptive/fixtures/nlu-calibration-stage-manifest-v1.json`
(SHA-256 `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`).
The source packet has passed 11/11 byte verification at 98,414 bytes. The
additional input is `nlu_candidate_bundle.py`, the local dependency imported
by the calibration release validator. The first ten-file staging attempt
failed closed at its import check and removed its incoming LXC directory.

Create only:

`/var/lib/aster-nlu-calibration/nlu-calibration-v1`

The parent and run directory must be root-owned mode `0700`; each of the eleven
inputs must be root-owned mode `0600`. Do not copy `labels.json`, policy
registration, threshold selection, cloud credentials, tools or the llama key.
Do not create `run.json` or `attempt-journal.jsonl` during staging.

## Bounded transaction

1. Recheck that neither the parent nor run directory exists, the llama service
   is active and the host has no active lease or competing maintenance.
2. Build a fresh owner-only Mac temporary packet from the exact existing
   sources. Validate all ten opened regular files against the frozen manifest.
3. Create one root-only `.incoming` directory in LXC110 and stream the eleven
   files over the established SSH transport. Do not persist a packet on the
   Proxmox host.
4. Recheck the exact name set, file type, owner, mode, size and SHA-256 inside
   LXC110 with the pinned staged-custody validator at SHA-256
   `8ea9daf47793aaeed0f2c475b4475cc1873173a9abc65089049e9c5bae86889e`.
   Run Python import/compile checks without invoking `main` or reading the
   service key.
5. Atomically rename `.incoming` to `nlu-calibration-v1` only after every
   check passes. Recheck the same properties at the final path.
6. Confirm there is no runner process, output/journal file, new listener,
   lease, model call or service restart; verify Aster, Speech and the accepted
   llama service remain healthy. Remove the Mac temporary packet.

If any check fails before the rename, remove only the new `.incoming`
directory and the Mac temporary packet. If post-rename state is uncertain,
retain the owner-only directory for reconciliation and do not run or retry it.
The private Mac source remains untouched in all cases.

## What this does not authorize

This staging step grants no inference or route authority. It does not authorize
the calibration run, lease acquisition, consumer isolation, service stop,
scoring, threshold selection, holdout creation/opening, shadowing, automatic
routing, cleanup of a used/uncertain run, or Git push.

After a staging pass, the next gate is the already approved 60-case run under a
compatible live lease. The lab-hours recovery chain remains the dependency for
that execution, not for this inactive copy.
