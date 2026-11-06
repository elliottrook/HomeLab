# M3 J2 isolated custody workspace recovery — 2026-11-06

## Outcome

The first external corpus and evaluation custody attempts are retained as
`NO-GO`. The corpus custodian could not find its Mac mini source workspace. The
evaluation custodian first reported an incomplete copied kit and then correctly
refused a retry because its MacBook destination already existed. Neither role
produced a key, receipt, proof or returned export.

The common failure was workspace durability. Both source kits and both return
directories had been staged under `/private/tmp` on the Mac mini. A Mac mini
crash/restart removed those paths. The already-created MacBook destination from
the failed evaluation copy then made the create-only retry fail closed.

## Recovery

Revision 2 was rebuilt under the Mac mini repository's ignored, persistent
`.aster-local-state` area:

- source root:
  `/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-kits-20261106-r2`;
- return root:
  `/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r2`;
- corpus archive SHA-256:
  `b0811a1f91c5c98c0553c6d30d8f7bf9efb0c831a3399fa9fcc25e5e836e1d30`;
- evaluation archive SHA-256:
  `60bcace51d33fcf6c3dd9716cfd7849f76d521f44456beb60ad1dd75653b6048`.

Both archives were independently extracted after creation. All 22
manifest-listed source files matched their recorded SHA-256 values. The corpus
archive contains the eleven exact staged inputs; the evaluation archive
contains only the one permitted corpus-comparison input. Both persistent return
directories exist with mode `0700`.

Fresh MacBook sessions must use new revision-2 destination names. They must not
reuse either failed session or its partially created destination. Archive
SHA-256 verification is required before extraction, and the source archive is
transferred as one file to prevent a partial recursive copy from looking like a
complete workspace.

The exact recovery prompts are the
[corpus remote revision-2 prompt](M3-J2-CORPUS-CUSTODIAN-REMOTE-R2-PROMPT-2026-11-06.md)
and the
[evaluation remote revision-2 prompt](M3-J2-EVALUATION-CUSTODIAN-REMOTE-R2-PROMPT-2026-11-06.md).

## Revision-2 dependency failure and revision 3

Both revision-2 roles then failed before producing an export because the kit
omitted `nlu_deterministic_guard_v1.py` and its dependency
`nlu_local_model_adapter.py`. Both attempts are terminal `NO-GO`; no corpus key
or evaluation seal was accepted.

The builder now includes both modules and tests the built entry point under
Python isolated mode. The focused builder/staging/custody suite passes 5/5.
Revision 3 was rebuilt in persistent storage, extracted independently, and
passed all 26 manifest hashes, both isolated imports and disposable keygen
probes. Verification-only keys are not present in the distributed archives.

- corpus archive SHA-256:
  `4b48afdcb68760d47af7b2342dd3696d8371c659d62b737efe7b97427dbe55cc`;
- evaluation archive SHA-256:
  `38ff8e6bd1a2d58134b676b819fc0ca7cd5c9096cb0f6e984f0281ab77d1527c`;
- source root:
  `/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-kits-20261106-r3`;
- return root:
  `/Users/jelliott/lab/homelab/.aster-local-state/aster-j2-isolated-custody-returns-20261106-r3`.

The only valid next attempts use the
[corpus revision-3 prompt](M3-J2-CORPUS-CUSTODIAN-REMOTE-R3-PROMPT-2026-11-06.md)
and the
[evaluation revision-3 prompt](M3-J2-EVALUATION-CUSTODIAN-REMOTE-R3-PROMPT-2026-11-06.md).

## Authority and exclusions

This recovery changes custody transport and durable staging only. It does not
accept either failed attempt, disclose private content, authorize training,
book Lab Hours, invoke a model, change routing, install trust or promote J2.
The normal two-role signature, distinct-key, disjointness and training-admission
checks remain mandatory after fresh exports return.
