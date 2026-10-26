# D4 candidate-G post-authority static preflight

**Date:** 2026-10-25  
**Decision:** STATIC GO; LIVE MODEL RUN STILL BLOCKED

The fixed Doctor authority path passed live activation, so Stream A rechecked
the already-approved and unspent candidate-G workload without acquiring a
lease, reading a credential, staging into a guest or calling the model.

## Exact static evidence

- Candidate-G dry-run status: `dry_run_valid`.
- Exact run digest:
  `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`.
- Eleven-file source manifest SHA-256:
  `defaf6039e01c7ac0cc16b3c2a28568336335bc949ea8992ec288819d33c23b8`.
- All 11 source lengths and SHA-256 values match that manifest.
- The dry run reported `keys_accessed=false`, 12 cases, at most 36 model calls,
  60-second request bounds, 180-second session bounds, no connected tools and
  no effects.
- The owner-only Mac packet remains mode `0600`, has exactly 11 members and
  SHA-256
  `d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`.

## Interpretation

The live fixed Doctor result closes the first capability-specific M1 authority
prerequisite. It does not turn candidate-G into a connected-tool run: the
candidate remains a frozen synthetic, tool-free development evaluation. Its
prior exact approval remains unspent because no model request or journal has
been created.

The live run still requires the same-cycle F2/F3/F4/F5 evidence, a corrected
executable F6 transaction with independent recovery, fresh runtime admission
and its already-recorded exact execution boundary. A failed or uncertain gate
means no model call. A 12/12 structural result only releases the conditional
blind review; it does not promote a model, route or tool authority.
