# M3 NLU Candidate-v7 calibration-v3 scoring/release receipt — 2026-10-26

> State: content-free release derived and validated; inference not authorized
>
> Authority: not granted
>
> Role: `stream-a-nlu-calibration-v3-scoring-operator`

## Scope

The scoring operator derived the sealed, content-free `nlu-calibration-v3`
release from the owner-only Candidate-v7 source, custody manifest and blind
labels. This receipt contains no request text, per-case labels, predictions,
model output, scores or holdout material.

## Exact input bindings

- case-source SHA-256:
  `b55098df5b7e475b4360007669d3c3b788fc89a1ab6eacaf023df0948bee4455`;
- label-artifact SHA-256:
  `07c9c99db496c338208378c1aa27ba3f2f46644e88cefb609fe9652a94848fa9`;
- custody-manifest SHA-256:
  `420507ab978d446d2f7ec2abab8fe93374485f4bbb989fdd9d27a971db4a71e6`;
- normalized-text-set SHA-256:
  `33fc068f2c259213ab53bf135770709802bc317f2661067380a2ad9e4e8c524c`;
- Candidate-v7 artifact SHA-256:
  `9987ac6cc7ebe948264701ae189f13c5e5f8eaabcd418d5839e892f1d17fe295`;
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
- release ID: `nlu-calibration-v3`;
- status: `sealed`;
- authority: `not-granted`;
- total cases: 60;
- family balance: ten cases in each of the six required request families;
- case custodian: `stream-a-nlu-calibration-v3-case-custodian`;
- label reviewer: `stream-a-nlu-calibration-v3-label-reviewer`;
- scoring operator: `stream-a-nlu-calibration-v3-scoring-operator`;
- canonical release self-hash:
  `3ffc3813451d5748c734bafe9eeaa6b7eb2c121f9e2d1fc9bbcab8192e0c05e8`;
  and
- exact release artifact SHA-256:
  `ca2d1838f34bb63e265b7fe3752856d84a4ee802dcc3117dd79f93695404582e`.

The owner-only release is stored outside Git at
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v3/release.json`
with mode `0600`. Its exact bytes were copied to
`scripts/aster-adaptive/fixtures/nlu-calibration-release-v3.json` with mode
`0644`. Byte comparison and independent SHA-256 checks confirmed the artifacts
are identical.

## Validation

- separate v3 derivation tool pins every input digest, including the custody
  manifest, without changing earlier versioned tools;
- focused v1/v2/v3 regression and derivation tests: 19 passed;
- release schema validator: no errors;
- embedded self-hash: matches the independently computed canonical hash;
- Candidate-v7, role, count and family bindings: exact;
- forbidden content-bearing keys: none; and
- source, label and manifest hashes after derivation: unchanged.

No model was called, no model output or score artifact was read, no candidate
quality was calculated, no prior labels, outputs, scores or releases were
accessed, no holdout was accessed, and no threshold, commit or remote operation
was performed. A separately authorized run remains required before inference.
