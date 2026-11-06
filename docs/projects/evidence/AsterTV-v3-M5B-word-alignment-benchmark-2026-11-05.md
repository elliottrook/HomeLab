# AsterTV v3 M5B word-alignment benchmark evidence

Date: 2026-11-05

Stream: SA-M5B

## Boundary

This is the one registered, hash-pinned eBook word-alignment benchmark
authorized by SA-M5B. It does not narrate the backlog, change the reader or
catalogue, create a recurring booking, expose book text or promote a timing
format.

## First booked attempt and fail-closed repair

Booking `astertv-v3-m5b-align-20261105-2310` was claimed by the authoritative
Lab Hours dispatcher and failed with `NO_GO` before inference. The transaction
restored production and retained the failed booking. The guest rejected the
four pinned faster-whisper snapshot entries because Hugging Face represents
them as symlinks to immutable cache blobs.

The correction permits a snapshot link only when strict resolution remains
inside `/root/.cache/huggingface/hub`, the resolved target is a regular,
single-link file within the size bound, and its SHA-256 equals the existing
pin. Links outside that cache, missing targets, non-regular files, additional
hard links and hash drift still fail closed. No model pin, input pin, runtime
pin, benchmark corpus or acceptance rule changed.

The repair was installed without creating a booking or starting a workload.
Its checkpoint is
`/var/lib/local-ai-lab/checkpoints/astertv-v3-m5b-model-custody-20261106T061716Z`.
The live fixed adapter and guest hashes are:

- adapter: `a17ff180a2f94a15d078caf56f9456e4ba5d9c132ce816577317b90a9fbeda28`
- guest: `24ad4300070c703068731192fac2502220a552f6acdc99d6d2a228205a997b92`

Twelve focused repository tests pass. Before the replacement window, the
whole-host lease reported `ready`, the EPUB worker was inactive, canonical
Aster Speech was active, and the authoritative dispatcher timer was enabled
and active.

## Replacement booking

The ledger reported the complete replacement execution and recovery window
clear before reservation.

- booking: `astertv-v3-m5b-align-20261105-2345`
- start: `2026-11-05T23:45:00-07:00`
- end: `2026-11-06T00:15:00-07:00`
- recovery reserve: 900 seconds
- owner: `astertv-v3-m5`
- workload: `astertv-v3-ebook-word-alignment-v1`

## Replacement result and restoration

The authoritative dispatcher claimed the replacement booking at 23:45:00.
It again failed closed before inference with `NO_GO`, this time because the
pinned virtual-environment interpreter path is a normal symlink to the exact
system interpreter. The resolved target is `/usr/bin/python3.13`, whose
SHA-256 is the already registered
`889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9`.
No word-alignment result was produced and nothing can be promoted.

The transaction restored production before closing the booking. Independent
postchecks found the whole-host lease `ready`, no drain or operation lock, the
EPUB worker inactive and canonical Aster Speech active. The content-free
booking record is retained as failed with result code `NO_GO`.

The repository candidate now accepts the virtual-environment interpreter link
only when strict resolution equals `/usr/bin/python3.13`, then applies the
unchanged size and SHA-256 pin to that regular target. A different target,
missing target, non-regular target or hash drift fails closed. Fourteen focused
M5B tests pass. Installing that second custody correction and booking another
attempt are not authorized by the completed replacement booking; they require
a new bounded decision.
