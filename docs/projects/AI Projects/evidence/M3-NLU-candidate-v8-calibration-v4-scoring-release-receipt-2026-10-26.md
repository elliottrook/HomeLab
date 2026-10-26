# M3 NLU Candidate-v8 calibration-v4 scoring/release receipt — 2026-10-26

> State: content-free release derived and validated; inference not authorized
>
> Authority: not granted
>
> Role: `stream-a-nlu-calibration-v4-scoring-operator`

## Scope

The scoring operator derived the sealed, content-free `nlu-calibration-v4`
release from the owner-only Candidate-v8 source, custody manifest and blind
labels. This receipt contains no request text, per-case labels, predictions,
model output, scores or holdout material.

## Exact input bindings

- case-source SHA-256:
  `09f82238506e01b8e8e2b443dfaee566263344a020032862cfb1570e958079c3`;
- label-artifact SHA-256:
  `daff07ce5521ccc9469a780c30ac5c625467435d84e21d1c760c05939cc50edb`;
- custody-manifest SHA-256:
  `12bb95b21c003ba43fbc40252eb8b6eee5eb3cb874690323cc953864d824f17d`;
- normalized-text-set SHA-256:
  `1a78b883cc5a39c88f96b5def07574c2ebe1821dfc17c15465ca80e87cbb906f`;
- Candidate-v8 artifact SHA-256:
  `033aa138e9995034d0ea19237f929e4dccab1c9341f0ff531e03ced84ac6d6a1`;
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
- release ID: `nlu-calibration-v4`;
- status: `sealed`;
- authority: `not-granted`;
- total cases: 60;
- family balance: ten cases in each of the six required request families;
- case custodian: `stream-a-nlu-calibration-v4-case-custodian`;
- label reviewer: `stream-a-nlu-calibration-v4-label-reviewer`;
- scoring operator: `stream-a-nlu-calibration-v4-scoring-operator`;
- canonical release self-hash:
  `f90aa4e1a8f24d4f2c5172c5d0a718560a2ad431c5091723b1f2d2e3b10182c2`;
  and
- exact release artifact SHA-256:
  `75bcffb8c6ef995e2b5e8ff09a5b8287790cdc418237282b03f3033af7e9a581`.

The owner-only release is stored outside Git at
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v4/release.json`
with mode `0600`. Its exact bytes were copied to
`scripts/aster-adaptive/fixtures/nlu-calibration-release-v4.json` with mode
`0644`. Byte comparison and independent SHA-256 checks confirmed the artifacts
are identical.

## Validation

- separate v4 derivation tool pins every input digest, including the custody
  manifest, without changing earlier versioned tools;
- focused v1–v4 regression and derivation tests: 23 passed;
- release schema validator: no errors;
- embedded self-hash: matches the independently computed canonical hash;
- Candidate-v8, role, count and family bindings: exact;
- forbidden content-bearing keys: none; and
- source, label and manifest hashes after derivation: unchanged.

No model was called, no model output or score artifact was read, no candidate
quality was calculated, no prior calibration labels, outputs, scores or
releases were accessed, no holdout was accessed, and no threshold, commit or
remote operation was performed. A separately authorized run remains required
before inference.
