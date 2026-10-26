# D4 fixed Doctor deterministic qualification v2 — 2026-10-26

## Result

The deterministic fixed Doctor response passed a fresh, independently
constructed synthetic qualification packet. All 12 cases passed all four
registered dimensions and contained zero unsafe claims. This qualifies the
fixed response architecture for an inactive production candidate. It does not
enable routing, grant a repair tool or authorize a service restart.

## Independence and custody

An independent custodian created 12 fictional cases after the deterministic
design was frozen: three each for `ok`, `warn`, `fail` and `unavailable`.
The questions have no exact overlap with the exposed v1 packet. The custodian
did not inspect the formatter or previous answers and reviews. The packet and
all answer/review artifacts remain owner-only outside Git at mode `0600`.

- source cases: 12, 5,645 bytes, SHA-256
  `a46398963e30ac20ee35b42b867ebc6716ff980eed02e0029cb3a162c2ea0e46`;
- deterministic attempts SHA-256
  `99b7eedb928256ab2046ac643ddeb020d55b0b112495f4e98e216fd6bc32b27c`;
- blind packet SHA-256
  `510a7363fb8d5b6004b98f063508b3814755765a6303f824812f3e49c4b1084e`.

A separate blind reviewer saw only the packet and blank review template. The
reviewer remained blind to candidate identity and acceptance outcome.

## Measured outcome

- state accuracy: `12/12`;
- evidence scope: `12/12`;
- freshness: `12/12`;
- limitation calibration: `12/12`;
- unsafe claims: `0`;
- review SHA-256:
  `ba31002ceb90c4e72ba16b99d3dc0ae692add96d0bcfcf3e5fa860b6b8a52c46`;
- accepted result SHA-256:
  `94cd3c3878866caafc7a6b69b42ae4cb749a0a032ca7226ade8ef11815c01aaa`.

The acceptance rule was exact: `12/12` passing cases and zero unsafe claims.
No model call was needed. The production-shaped renderer is checked for exact
output equivalence against the qualified formatter across all 12 sealed cases.

## Next boundary

The next step is a hash-pinned inactive installation candidate for the
production renderer and its caller integration. Installation must leave the
running services unchanged. A later cutover that restarts Aster or the fixed
Doctor caller remains a separate explicit restart decision.
