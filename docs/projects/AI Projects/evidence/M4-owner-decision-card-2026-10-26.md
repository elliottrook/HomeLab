# M4 owner decision card — synthetic evidence loop

**Prepared:** 2026-10-26  
**Status:** retained by owner on 2026-10-27; external human-controlled custody confirmed

Jason selected `retain` and confirmed that the three fixed identifiers below
were copied to a human-controlled offline record. The repository
[acceptance transcription](M4-review/owner-acceptance-2026-10-27.json) binds
that decision to the reviewed commit, artifact and ledger head. The external
record remains the independently controlled custody object; this JSON is its
bounded validation copy, not a replacement for it.

## Exact decision

Choose one of `retain`, `reject` or `request-more-evidence` for the current
**synthetic-only offline evidence procedure**. A `retain` decision means the
164-event artifact, verifier and storage/review design may remain the accepted
M4 baseline for later experiments. It does not approve a collector, private
data, a learned route, a model promotion, a deployment or any authority.

## Independently checked object

- reviewed candidate commit:
  `af2cc4f988ca9ed1a69e0d425c2bb7991ffa7f71`
- measurement artifact SHA-256:
  `9a3e0447adbf27f24bf5d9ab777ebbd5565bbce7873f554034304a4ce88fea38`
- ledger head:
  `sha256:59fa02fe1a196ba123c447d4e773bd9404290970f4446113c8dd61b1b12cc7c9`
- verifier SHA-256:
  `9b04d938a79c6c2c61a2b4328b77d2f3b4292fee066cca1b5c7500071f8b8af7`

The verifier reconstructed all 164 events, reproduced four passing synthetic
families and reported `measurement_authenticity: not-established` and
`review_approval: not-granted`. Six reconstruction/acceptance tests pass. This
proves structural and arithmetic reproducibility only.

## Required external custody action

Before `retain` counts as M4 acceptance, Jason must copy the reviewed commit,
artifact digest and ledger head above into one record outside this repository
and outside the experiment writer's control. A personal password-manager note,
an independently controlled account/device or a physical record is sufficient.
Do not include a credential or signing key.

The response should name only the custody method, not a secret or location. For
example: `retain; copied to a human-controlled offline record`. Stream A can
then record the decision and validate its exact shape while keeping the
external record itself outside Git.

## Limits that remain binding after retain

- synthetic provenance only; measurement authenticity remains unestablished;
- no real prompt, private source output, identifier, embedding, credential or
  approval material may be collected under this decision;
- no collector, schedule, identity, service, model, route or access grant is
  created;
- a future real-data pilot needs explicit purpose, consent, access, numeric
  retention, backup and deletion rules;
- authority remains `not-granted` and promotion remains a separate decision.

The required external copy and owner judgment are now complete for this exact
synthetic-only baseline. Additional synthetic runs are not required to close
M4, and none can expand the limits above.
