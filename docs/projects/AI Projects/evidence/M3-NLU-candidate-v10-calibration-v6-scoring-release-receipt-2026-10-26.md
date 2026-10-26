# M3 NLU Candidate-v10 calibration-v6 scoring/release receipt — 2026-10-26

> State: content-free release derived and validated; inference not authorized
>
> Authority: not granted
>
> Role: `stream-a-nlu-calibration-v6-scoring-operator`

## Scope

The scoring operator derived the sealed, content-free `nlu-calibration-v6`
release from the owner-only Candidate-v10 source, custody manifest and blind
labels. This receipt contains no request text, per-case labels, predictions,
model output, scores or holdout material.

## Exact input bindings

- case-source SHA-256:
  `a0a85ba1e46e88c0a7557dcd8744530d336bef74f5cd1854d25ba31877a5da4d`;
- label-artifact SHA-256:
  `c34ed167367d9b36023e084f764ef792e808ba575277e3c419cee429b7a3b5a1`;
- custody-manifest SHA-256:
  `792ced736411d4cb3799da504cfcbe5b2db57c2554d6e8447b7c05e9615fa404`;
- normalized-text-set SHA-256:
  `76a9d7164f63878babf6ef7fe4d836eb7270cbca8bc6a776cc60e93e3f438b6e`;
- Candidate-v10 artifact SHA-256:
  `ad01b3883a65125b1e37335b66d62a65d65103b98c8577ecd2a337833a2bcb39`;
- accepted decision artifact SHA-256:
  `8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da`;
  and
- public development fixture SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`.

The private source directory was mode `0700`; the cases, labels and custody
manifest were mode `0600`. Every supplied digest matched immediately before
derivation, and the release destination did not exist.

## Release identity

- schema: `aster-nlu-calibration-release.v1`;
- release ID: `nlu-calibration-v6`;
- status: `sealed`;
- authority: `not-granted`;
- total cases: 60;
- family balance: ten cases in each of the six required request families;
- case custodian: `stream-a-nlu-calibration-v6-case-custodian`;
- label reviewer: `stream-a-nlu-calibration-v6-label-reviewer`;
- scoring operator: `stream-a-nlu-calibration-v6-scoring-operator`;
- canonical release self-hash:
  `7923044977bece755ac6a534ccaf740363b55bc89b02ec02bfdc9ce723bc3c2d`;
  and
- exact release artifact SHA-256:
  `7b071050d4ac1db04b3b2d8a6202ec4c54293c4b80c9f6a7c907b89e6acd2c8e`.

The owner-only release is stored outside Git at
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v6/release.json`
with mode `0600`. Its exact bytes were copied to
`scripts/aster-adaptive/fixtures/nlu-calibration-release-v6.json` with mode
`0644`. Byte comparison and independent SHA-256 checks confirmed the artifacts
are identical.

## Validation

- separate v6 derivation tool pins every input digest, including the custody
  manifest, without changing earlier versioned tools;
- focused v1–v6 regression and derivation tests: 31 passed;
- release schema validator: no errors;
- embedded self-hash: matches the independently computed canonical hash;
- Candidate-v10, role, count and family bindings: exact;
- forbidden content-bearing keys: none; and
- source, label and manifest hashes after derivation: unchanged.

No model was called, no model output or score artifact was read, no candidate
quality was calculated, no prior calibration labels, outputs, scores or
releases were accessed, no holdout was accessed, and no threshold, commit or
remote operation was performed. A separately authorized run remains required
before inference.
