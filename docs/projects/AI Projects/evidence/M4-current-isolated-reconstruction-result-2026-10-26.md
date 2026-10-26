# M4 current isolated reconstruction result — 2026-10-26

**Result:** **PASS for technical reconstruction; independent acceptance remains open**

The historical M4 manifests still correctly pin their original source and
evidence snapshots. Several shared source files have since evolved, so those
historical manifests cannot also describe the current reconstruction toolchain.
They were preserved unchanged.

A new current-state manifest pins the current verifier, store, contracts,
paired evaluator, the immutable 164-event synthetic export, Python 3.12.14 and
Pydantic 2.14.1. The reconstruction tool verifies each regular file before
copying only those files into a fresh temporary directory, invokes the offline
verifier there, and removes the directory afterward. It never executes the
measurement runner.

Measured result:

- 164 events reconstructed;
- export SHA-256
  `9a3e0447adbf27f24bf5d9ab777ebbd5565bbce7873f554034304a4ce88fea38`;
- verified ledger head
  `sha256:59fa02fe1a196ba123c447d4e773bd9404290970f4446113c8dd61b1b12cc7c9`;
- exactly one paired evaluation recovered;
- measurement authenticity: `not-established`;
- review approval: `not-granted`;
- authority: `not-granted`.

The focused evidence/reconstruction suite passes 31/31. This closes M4's
current technical isolated reconstruction and final source/evidence
reconciliation. It does not establish independent checkpoint custody, human
review, storage-design acceptance, private-data retention, collection,
deployment or promotion. Those trust and operational decisions remain separate.

