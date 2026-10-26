# M3 NLU Candidate-v8 calibration-v4 case custody receipt — 2026-10-26

> State: fresh case creation complete; independent labels and holdout
> non-overlap pending
>
> Authority: not granted

## Custody and binding hashes

- Private source path identifier:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v4`
- Directory mode: `0700`
- Source-file modes: `0600`
- Sealed Candidate-v8 artifact SHA-256:
  `033aa138e9995034d0ea19237f929e4dccab1c9341f0ff531e03ced84ac6d6a1`
- Accepted decision artifact SHA-256:
  `8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da`
- Case-source SHA-256:
  `09f82238506e01b8e8e2b443dfaee566263344a020032862cfb1570e958079c3`
- Case-source bytes: `7238`
- Custodian-design SHA-256:
  `fc1d3b51b4e3e47e28cd6907d6cae8eaeb185f2b542a6c8cdfc363246a7b0b5b`
- Custody-manifest SHA-256:
  `12bb95b21c003ba43fbc40252eb8b6eee5eb3cb874690323cc953864d824f17d`
- Normalized-text-set SHA-256:
  `1a78b883cc5a39c88f96b5def07574c2ebe1821dfc17c15465ca80e87cbb906f`

## Counts

- Total cases: `60`
- Unique normalized texts: `60`
- `household-command`: `10`
- `general-answer`: `10`
- `read-only-investigation`: `10`
- `change-request`: `10`
- `external-research`: `10`
- `unsupported`: `10`

## Aggregate contract coverage

- public references: `20`
- internal references: `27`
- personal references: `13`
- clear wording: `51`
- ambiguous wording: `9`
- single intent: `38`
- mixed intent: `16`
- changed intent: `6`
- safe route target: `36`
- safe clarify target: `9`
- safe abstain target: `9`
- safe deny target: `6`

## Aggregate prior-failure-class coverage

- rollback-copy destruction inside a change: `2`
- ambiguous supported-request capability retention: `2`
- pure private-data publication family: `2`
- mixed-intent final-correction family: `5`
- negated-action capability assignment: `3`
- private calendar versus other private-record capability mapping: `1`
- multi-source local join: `2`
- public-web plus private-source join: `2`
- structurally invalid JSON response: `1`

## Disjointness and content checks

- Public development fixture SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`
- Candidate-v1 calibration source SHA-256:
  `6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e`
- Candidate-v6 calibration-v2 source SHA-256:
  `c865bb045fa157592429bf1c4bd20a5aadd7a3f8b40ed0aaa536150a300334df`
- Candidate-v7 calibration-v3 source SHA-256:
  `b55098df5b7e475b4360007669d3c3b788fc89a1ab6eacaf023df0948bee4455`
- Normalized-text overlap with each comparison source: `0`
- Duplicate Candidate-v8 calibration-v4 normalized texts: `0`
- Credential, contact and network-pattern hits: `0`

No request text or interpretation label is stored in this receipt. The case
custodian read only prior request-source text for normalized overlap and used
only the separately supplied aggregate failure-class names. The custodian did
not access prior labels, model output, scores, releases, or any holdout
material and did not act as label reviewer or scoring operator.
