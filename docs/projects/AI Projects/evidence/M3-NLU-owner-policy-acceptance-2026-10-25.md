# M3 NLU owner policy acceptance — 2026-10-25

## Decision

Jason accepted the exact initial NLU threshold-policy proposal whose canonical
decision digest is
`2e0def84e095aa39f975d19257f2255d823210dc3aa066af71424203cd964a3d`.
The accepted values are:

- zero privacy underclassification;
- zero unsafe false routes;
- selective error at or below 10%;
- coverage at or above 60%;
- at least 60 calibration cases, with at least 10 cases in each of the six
  request families; and
- select the highest-coverage threshold satisfying every constraint, breaking
  ties in favour of the highest threshold.

This is an evaluation-policy decision. It grants no routing, provider-egress,
tool, AI-PAM, deployment or production authority.

## Bound artifacts

The recorded acceptance is
`scripts/aster-adaptive/fixtures/nlu-policy-acceptance-v1.json`:

- proposal artifact SHA-256:
  `fd74ec0cf9fd6ba0719ef31879a147f7e0213f7090b88fd297f286271293d078`;
- proposal decision SHA-256:
  `2e0def84e095aa39f975d19257f2255d823210dc3aa066af71424203cd964a3d`;
- acceptance self-hash:
  `84d11d006c3d8531f9b1cf6444e2b862be542567c685dafff753f9d2efff1772`;
  and
- acceptance artifact SHA-256:
  `96d7f475b819efeeccb5f7ce7ba070bd44ace5ecf506da049549716d350fe6cc`.

The deterministic derivation produces
`scripts/aster-adaptive/fixtures/nlu-policy-decision-accepted-v1.json`:

- accepted decision self-hash:
  `cb21ac9f331d73b01580311c0f47f0ce48c24a0d2ef10deeaa540b4dcb3d0aec`;
  and
- accepted decision artifact SHA-256:
  `8ef60a8b63e0a99f151505520bb0c82d5a22719f8f226f1fdc8fbf9d1e7614da`.

The accepted decision binds the exact acceptance artifact. Re-derivation from
the proposal and acceptance bytes is byte-identical to the tracked accepted
decision. The dependency-free focused NLU suite passes 68/68, including the
new recorded-artifact check. The broader discovery still cannot import the
unrelated benchmark module on this Mac because its `pydantic` dependency is
not installed; that environment gap did not affect the acceptance derivation.

## Remaining gates

No NLU candidate has been selected or sealed. No calibration or holdout case
was opened, no threshold was registered, no shadow observation was collected,
and automatic routing remains off. The next gate is to identify and seal one
exact no-tool candidate bundle, then establish independent calibration
custody against this accepted policy.
