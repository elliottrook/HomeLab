# M3 NLU Candidate-v9 calibration-v5 scoring/release receipt — 2026-10-26

> State: content-free release derived and validated; inference not authorized
>
> Authority: not granted
>
> Role: `stream-a-nlu-calibration-v5-scoring-operator`

## Scope

The scoring operator derived the sealed, content-free `nlu-calibration-v5`
release from the owner-only Candidate-v9 source, custody manifest and blind
labels. This receipt contains no request text, per-case labels, predictions,
model output, scores or holdout material.

## Exact input bindings

- case-source SHA-256:
  `50b6a36b64e8942eb83dd8769f52c52b6fa4a0e7a1d42adeebd7be2c5157c676`;
- label-artifact SHA-256:
  `5cf947586cac331efe08f375a4a22aceca0ea0f9b1bea92ae466a0fec2a811ae`;
- custody-manifest SHA-256:
  `87e1a39de0fe7f6ef6585f51727f131251df6ad665108b843c4d9ab2db544e8b`;
- normalized-text-set SHA-256:
  `be93e28afa6de2a5a6c525c1659563292196c05a84bcff1412b38795d39d2423`;
- Candidate-v9 artifact SHA-256:
  `1941b4754c5195e11b623479f63cb368cacfea64a7adc3223bf22794e3b825f5`;
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
- release ID: `nlu-calibration-v5`;
- status: `sealed`;
- authority: `not-granted`;
- total cases: 60;
- family balance: ten cases in each of the six required request families;
- case custodian: `stream-a-nlu-calibration-v5-case-custodian`;
- label reviewer: `stream-a-nlu-calibration-v5-label-reviewer`;
- scoring operator: `stream-a-nlu-calibration-v5-scoring-operator`;
- canonical release self-hash:
  `0bc91001202360b76661c0a50e914e7fee948e7d3a4c06768eab52378830e11f`;
  and
- exact release artifact SHA-256:
  `a407bf3e7939e685ae69a80b2d74bafb89b4d4719652281a87b04d572a548896`.

The owner-only release is stored outside Git at
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v5/release.json`
with mode `0600`. Its exact bytes were copied to
`scripts/aster-adaptive/fixtures/nlu-calibration-release-v5.json` with mode
`0644`. Byte comparison and independent SHA-256 checks confirmed the artifacts
are identical.

## Validation

- separate v5 derivation tool pins every input digest, including the custody
  manifest, without changing earlier versioned tools;
- focused v1–v5 regression and derivation tests: 27 passed;
- release schema validator: no errors;
- embedded self-hash: matches the independently computed canonical hash;
- Candidate-v9, role, count and family bindings: exact;
- forbidden content-bearing keys: none; and
- source, label and manifest hashes after derivation: unchanged.

No model was called, no model output or score artifact was read, no candidate
quality was calculated, no prior calibration labels, outputs, scores or
releases were accessed, no holdout was accessed, and no threshold, commit or
remote operation was performed. A separately authorized run remains required
before inference.
