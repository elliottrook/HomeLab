# V5 accepted-corpus candidate — operations plan

Status: **FROZEN LOCALLY / NOT AUTHORIZED FOR STAGING OR EXECUTION**  
Run identity: `corpus-descriptive-001`  
Proposed fresh VM: 122, `aster-s0-corpus-v1`

## Purpose and claim boundary

Run the already accepted, exposed 30-family S0 pilot exactly once to obtain
descriptive integration and error evidence for three deterministic standard-library
routers. This can describe behavior on 20 train and 10 development families. It
cannot establish generalization, calibration, production accuracy, privacy safety,
model selection, tool authority or permission to promote any route.

The candidate includes the nine hash-bound proposal/acceptance/effort artifacts,
the existing adapter and keyword/nearest implementation, and a new bounded worker.
No real request, secret, credential, model, GPU, cloud call, tool call, production
service or network device is included. The guest result explicitly declines to
claim approval or promotion; authority remains in the external human approval
record and deterministic release controls.

## Fixed comparison

- Engines: always abstain; existing keyword rules; TF-IDF nearest at fixed 0.2.
- Profiles: request only; request plus verbatim synthetic context.
- One semantic pass per engine/profile over ten development families.
- Thirty warm timing repeats, which are timing samples rather than new evidence.
- All ten development cases stay in each denominator. Errors remain failures.
- Confidence, privacy-routing quality, cloud requirement and production local
  resolution remain null because this experiment does not measure them.

The dataset-manifest digest is
`c3d26c6685d7056fbd70d28d08f800abe5148e5d02b7162cadc9709c04373353`.
The payload-manifest digest is
`4c6abae20160875196a2a94d998f0cba7553199876f1f88b9687d4410c95fd9d`.

## Boundary and lifecycle

Use a fresh import of the pinned Debian image and a fresh NoCloud ISO. VM122 has one
vCPU, 1 GiB fixed RAM, an 8-GiB non-backed-up OS disk, serial console and no vNIC,
agent, shared filesystem, passthrough or credential. The worker runs unprivileged
with private network/devices/tmp, read-only system and corpus/source paths, one
task, 384-MiB/no-swap memory, 50% CPU, 70 CPU seconds, 75 wall seconds, 4-MiB file
and 64-descriptor bounds.

The outer host capture is limited to 300 seconds and 4 MiB. It performs no retry.
The guest powers off after publishing one digest-bound result. At the deadline the
host may stop only VM122, then retains it and all evidence. VMs118–121 must remain
stopped and untouched.

## Pass and stop rules

A structurally valid run requires exact artifact hashes, exact VM configuration,
one complete protocol envelope, exact run/payload identity, canonical result JSON,
all ten development IDs for every engine/profile, no row/engine errors, 300 warm
samples per engine/profile, no budget stop and a stopped VM. Low router agreement
is a valid negative result and must not cause retry.

Any hash/configuration/protocol/budget/lifecycle mismatch is failed or inconclusive.
Retain it; do not repair in place, reboot, tune the threshold, relabel cases, change
the split, remove failures or run another candidate under the same approval.

## Exclusions

Remote staging, ISO/VM creation, boot, evaluation, cleanup, deletion and Git push
are not authorized by this local packet. No result can promote an engine, alter a
policy or permission, or unlock production routing automatically.
