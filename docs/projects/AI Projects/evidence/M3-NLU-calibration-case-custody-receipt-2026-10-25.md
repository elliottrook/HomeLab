# M3 NLU calibration case custody receipt — 2026-10-25

> State: case creation complete; independent labels completed separately;
> future holdout non-overlap pending
>
> Authority: not granted

## Custody

- Custodian role: `stream-a-nlu-calibration-case-custodian-v1`
- Private source path identifier:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/nlu-calibration-v1`
- Directory mode: `0700`
- Source files: owner mode `0600`
- Case-source SHA-256:
  `6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e`
- Case-source bytes: `7049`
- Custodian-design SHA-256:
  `531912a18cbd897f19daaef98cfb5ed688cecdb7ea389684fac2e62c355c61d6`
- Custody-manifest SHA-256:
  `a7aec55579cfcf0fde952c6117fcf1f4d7a97001f296f89884c0292a06ae8d4d`
- Normalized-text-set SHA-256:
  `c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3`

## Counts

- Total cases: `60`
- Unique normalized texts: `60`
- `household-command`: `10`
- `general-answer`: `10`
- `read-only-investigation`: `10`
- `change-request`: `10`
- `external-research`: `10`
- `unsupported`: `10`

## Coverage metadata

- public references: `19`
- internal references: `28`
- personal references: `13`
- clear wording: `48`
- ambiguous wording: `12`
- single intent: `35`
- mixed intent: `19`
- changed intent: `6`
- safe route target: `35`
- safe clarify target: `11`
- safe abstain target: `8`
- safe deny target: `6`

## Disjointness and content checks

- Exposed development fixture SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`
- Exact normalized-text overlap with its 24 cases: `0`
- Duplicate calibration normalized texts: `0`
- Credential, contact and network-pattern hits: `0`

No request text or interpretation label is stored in this receipt. The case
custodian did not access model output or the independent holdout and did not
act as label reviewer or scoring operator.
