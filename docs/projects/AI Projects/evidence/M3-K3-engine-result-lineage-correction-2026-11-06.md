# M3 K3 engine-result lineage correction — 2026-11-06

## Result

Platform composition review found that the K3 runtime manifest and guest
admission pinned the accepted 9B model artifact, but the retained K3 run object
did not repeat that digest. Commit `dd6cd011` closes the evidence-lineage gap:
every K3 run now emits `engine_sha256` equal to the frozen accepted model digest,
and the complete runner test verifies it.

The corrected identities are:

- runner SHA-256:
  `940d1de888bc00709f37db09604bd7062dbd9553dbdc970e7d9c8d705378bf96`;
- runner test SHA-256:
  `f8d05081afcaaa006ec25311d3a8aa606ab98144eac15f507399f9b2b48e9820`;
- runtime manifest SHA-256:
  `0a9866a10c4079879fc7d7e8298969074cc50e44b36afd3b1c56e570fe08fa45`.

The focused and complete K3/K-series suites remain 21/21 and 145/145. No model
request, platform mutation, booking, service action, sealed access, route or
promotion occurred. Platform registration must use only these corrected pins.
