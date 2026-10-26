# M3 NLU Candidate-v6 calibration-v2 scoring/release receipt — 2026-10-26

> State: content-free release derived and validated; inference not authorized
>
> Authority: not granted
>
> Role: `stream-a-nlu-calibration-v2-scoring-operator`

## Scope

The scoring operator derived the sealed, content-free `nlu-calibration-v2`
release from the fresh private Candidate-v6 source and independently reviewed
blind labels. This receipt contains no request text, per-case labels,
predictions, model output, scores or holdout material.

## Exact input bindings

- case-source SHA-256:
  `c865bb045fa157592429bf1c4bd20a5aadd7a3f8b40ed0aaa536150a300334df`;
- label-artifact SHA-256:
  `5a200f835dcbbba1b4b1d533951755cef7f4ee26131afbdd6263c0439bb1594f`;
- Candidate-v6 artifact SHA-256:
  `6a16f92527981d5048a4163b5c8de2ad146ec7901f459d221f628e663d06c236`;
- accepted decision artifact SHA-256:
  `8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da`;
- public development fixture SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`;
  and
- normalized-text-set SHA-256:
  `71d5154563adb5ba360fa79aca468e87319f8e8b29f4c2ed0bbf2d2305257fdb`.

The private source directory was mode `0700`; the source and label files were
mode `0600`. Their hashes matched the handoff immediately before derivation,
and the release destination did not exist.

## Release identity

- schema: `aster-nlu-calibration-release.v1`;
- release ID: `nlu-calibration-v2`;
- status: `sealed`;
- authority: `not-granted`;
- total cases: 60;
- family balance: ten cases in each of the six required request families;
- case custodian: `stream-a-nlu-calibration-v2-case-custodian`;
- label reviewer: `stream-a-nlu-calibration-v2-label-reviewer`;
- scoring operator: `stream-a-nlu-calibration-v2-scoring-operator`;
- canonical release self-hash:
  `406a50ac9e889102ab4e22a28a5c949613be699863d0b4e2d5853a6540f9a02d`;
  and
- exact release artifact SHA-256:
  `191bc3e11da4df1eb9716f2bf6b82c0b50ced5ab911a4fb22653b755dc6a0e8f`.

The owner-only release is stored outside Git at
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v2/release.json`
with mode `0600`. Its exact bytes were copied to
`scripts/aster-adaptive/fixtures/nlu-calibration-release-v2.json` with mode
`0644`. Byte comparison and independent SHA-256 checks confirmed the artifacts
are identical.

## Validation

- separate v2 derivation tool pins every input digest and leaves v1 behavior
  unchanged;
- focused v1 regression and v2 derivation tests: 15 passed;
- release schema validator: no errors;
- embedded self-hash: matches the independently computed canonical hash;
- Candidate-v6, role, count and family bindings: exact;
- forbidden content-bearing keys: none; and
- source and label hashes after derivation: unchanged.

No model was called, no model output or score artifact was read, no candidate
quality was calculated, no earlier candidate release or labels were accessed,
no holdout was accessed, and no threshold, commit or remote operation was
performed. A separately authorized run remains required before inference.
