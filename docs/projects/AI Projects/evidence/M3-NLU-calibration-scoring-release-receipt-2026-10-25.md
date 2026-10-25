# M3 NLU calibration scoring/release receipt — 2026-10-25

> State: release derived and validated; inference not authorized
>
> Role: `stream-a-nlu-calibration-scoring-operator-v1`

## Scope

The scoring operator derived the content-free `nlu-calibration-v1` release from
the separately frozen private cases and labels. This receipt contains no case
text, labels, predictions, model output or holdout material and grants no
authority to run inference, select a threshold or enable routing.

## Inputs verified immediately before derivation

- private case source SHA-256:
  `6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e`;
- private label source SHA-256:
  `b2cb80b0f4aa24b466980b898638895b6e9e67de745c5e6ecf9ef9d2b1b14031`;
- private input modes: `0600` for both files;
- public development fixture SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`;
  and
- public development fixture mode: `0644`.

The private case and label digests matched the creation handoff exactly. The
release destination did not exist before the single derivation invocation.

## Derived release

- schema: `aster-nlu-calibration-release.v1`;
- release ID: `nlu-calibration-v1`;
- status: `sealed`;
- authority: `not-granted`;
- case count: 60, with ten cases in each required request family;
- normalized-text-set SHA-256 for later holdout exclusion:
  `c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3`;
- canonical release self-hash:
  `e3a77d3dd0f63626f43704d8242195b56b94529066cafb74ac6f5a1edb86eaf2`;
  and
- exact release artifact SHA-256:
  `f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1`.

The owner-only release is stored outside Git as mode `0600`. Its exact bytes
were copied to
`scripts/aster-adaptive/fixtures/nlu-calibration-release-v1.json`, with the Git
fixture stored as mode `0644`. A byte comparison and independent SHA-256 checks
confirmed the two files are identical.

## Validation

- focused calibration corpus and release tests: 11 passed;
- release schema validator: no errors;
- embedded `release_sha256`: matches the independently computed canonical
  self-hash;
- content scan: no forbidden content-bearing keys; and
- custody boundary: no model was called, no candidate quality was calculated,
  no holdout was accessed, and no threshold was registered or frozen.

This release remains evidence only. A separate exact run card and bounded
model-call approval are required before inference.
