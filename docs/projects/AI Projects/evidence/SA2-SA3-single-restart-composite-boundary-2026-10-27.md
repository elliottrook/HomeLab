# SA2/SA3 single-restart composite boundary — 2026-10-27

Status: **source-complete; no live effect**

## Purpose

The reviewed SA3 candidate-E gateway and the reviewed SA2 fixed Doctor-status
producer were independently ready for target checks, but their separate install
cards each required an Aster Agent restart. This packet composes the exact two
reviewed releases into one atomic seven-file installation and one successful
service restart. It does not merge their authority: candidate E can only journal
a no-effect proposal, while the Doctor producer can only execute the fixed
`homelab-doctor/status` observation selected by an exact pending decision.

## Exact source boundary

- composite manifest SHA-256:
  `2eb2499d3051d772befce0b087b2f52264370d18398248b9445c6223fa622aea`;
- validator SHA-256:
  `4c9b32eba3687fbfe6dda0f59f358ef2dbec9f100e83692e73ed9f49d36a820d`;
- deterministic builder SHA-256:
  `82af99e6c41fed2e608b43fb1405b218ab654b582561475ed2f1d4663a73eca0`;
- installer SHA-256:
  `feb61c286df6bf86f6ca95185c22e82702d51fa01435f7443bb25927bb21dc6f`;
- focused test SHA-256:
  `44f604fc8000145bf69c4fac1e453b3bf8eaa2dc75b0a9ecec943ad112eeb841`;
- deterministic packet SHA-256:
  `b03586e9ee9bf59de0c94aa6e78afa832dc10a28169d718f4a85dc024d63bfcb`.
- target-validation packet builder SHA-256:
  `1e5bcac28a7f58398b2510375f060dcb6dd42bbdf17edaaa6a92dc85c8fb9bf1`;
- target-validation packet test SHA-256:
  `66472c04cb7abe9dafa4a2a14a424886543804cac111fe416146c9b7c5fdb436`;
- the original 16-member target packet omitted the shared synthetic fixture
  required by two test modules and is rejected by the October 28 live
  preflight. The corrected deterministic 17-member packet includes only that
  pinned fixture in addition to the original candidate and test members; its
  replacement digest is recorded in the target-preflight result.

The manifest pins the exact reviewed component manifests at SHA-256
`d65cab04…c641` and `15bc7593…a82`. The builder validates both components,
opens each candidate once without following links, requires a single-link
regular file, hashes the bytes it read and archives those same bytes. The flat,
private archive has exactly seven members and deterministic metadata.

## Transaction and rollback

The installer requires the four exact live predecessors and the three proposal
modules to be absent. It checkpoints all four replacements before staging,
imports the complete candidate against target Python before the first write,
installs the seven files atomically, and restarts only `aster-agent.service`.
Postchecks require fixed health, no restart failure, unauthenticated denial at
model discovery and both new routes, exact hashes and root-owned mode `0644`
custody.

Failure after the first live rename restores all four predecessors, removes
only the three additions, restarts only Aster Agent and waits for health. The
accepted llama.cpp/SYCL service is never changed or restarted.

## Validation

- composite and component manifest/packet/installer suite: **30/30 passed**;
- shell syntax: **pass**;
- manifest reports seven files, one normal-path restart, automatic routing
  false and repair authority false;
- a temporary archive reproduced the exact packet digest and member set, then
  was removed;
- no LAN query, deployment, restart, model request, lease, schedule change or
  automatic route occurred.

## Remaining live gate

After the protected overnight window, re-read all four live predecessor hashes
and confirm the three additions remain absent. Build the exact packet, run the
complete temporary target-Python suite from the deterministic 16-member
candidate-and-test packet, remove temporary staging and recheck production. If
those checks pass, one explicit approval covers the exact
composite installation and its single Aster Agent restart. This packet does not
authorize that effect.
