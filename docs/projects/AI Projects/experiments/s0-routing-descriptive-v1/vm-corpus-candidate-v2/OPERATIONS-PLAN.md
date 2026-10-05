# V5b corrected accepted-corpus candidate — operations plan

Status: **FROZEN LOCALLY / NOT AUTHORIZED FOR STAGING OR EXECUTION**
Run identity: `corpus-descriptive-002`
Proposed fresh VM: 123, `aster-s0-corpus-v2`

## Purpose and correction boundary

Retry the already approved descriptive S0 question with a new immutable identity
after V5 failed before evaluation. VM122 forensics proved the V5 package omitted
`validate_label_batch.py`: every frozen input hash was verified, but import failed
before JSON parsing, adaptation, engine construction or routing.

V5b changes only the packaging and ineffective limit declaration:

- package and hash-bind `validate_label_batch.py` with the other three sources;
- statically require every imported sibling module to be in the source bundle;
- prove the generated source bundle imports under Python's guest `-I -S -B` flags;
- remove `RuntimeMaxSec=75`, which systemd ignores for `Type=oneshot`; and
- advance the run, instance, hostname, ISO and proposed VM identities.

The nine corpus artifacts, their hashes and split, the three engines, fixed 0.2
threshold, two profiles, result contract, security controls and effective resource
bounds are unchanged. This correction does not tune or relabel anything.

## Claim boundary and fixed comparison

The run can produce descriptive integration and error evidence for 20 training and
10 development families. It cannot establish generalization, calibration,
production accuracy, privacy safety, model selection, tool authority or promotion.

- Engines: always abstain; existing keyword rules; TF-IDF nearest at fixed 0.2.
- Profiles: request only; request plus verbatim synthetic context.
- One semantic pass over ten development families per engine/profile.
- Thirty warm timing repeats, treated as timing samples rather than new evidence.
- All development cases remain in each denominator; failures remain failures.

Dataset-manifest SHA-256:
`c3d26c6685d7056fbd70d28d08f800abe5148e5d02b7162cadc9709c04373353`.
Payload-manifest SHA-256:
`dc2a9274ae01c6c56c2216f6ae151f96eecd748103e57dce5638d661879165c0`.

## Boundary and lifecycle

VM123 uses a fresh import of the pinned Debian image and a fresh NoCloud ISO. It
has one vCPU, 1 GiB fixed RAM, an 8-GiB non-backed-up disk, serial console and no
vNIC, agent, shared filesystem, passthrough or credential. The unprivileged unit
retains private network/devices/tmp, read-only input paths, one task, 384-MiB
memory with no swap, 50% CPU quota, 70 CPU seconds, a 75-second start deadline,
4-MiB file limit and 64-descriptor limit.

The host capture remains bounded to 300 seconds and 4 MiB. It performs no retry.
The guest powers off after publishing at most one digest-bound result. At deadline
the host may stop only VM123 and must retain it and all evidence. VMs118–122 remain
stopped and untouched.

## Pass, stop and authority rules

A structurally valid run requires exact artifact hashes and VM configuration, one
complete protocol envelope, exact run/payload identity, canonical JSON, all ten
development IDs for every engine/profile, no row or engine errors, 300 warm samples
per engine/profile, no budget stop and a stopped VM. Low agreement is valid negative
evidence and cannot trigger a retry.

Any mismatch is failed or inconclusive. Retain it without in-place repair, reboot,
tuning, relabeling or another candidate under the same approval. Remote staging,
ISO/VM creation, boot, evaluation, cleanup, deletion and Git push require their
own authority. No result can promote an engine or alter policy or permissions.
