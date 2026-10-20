# F3/F4 conditional sequence — independent review, 2026-10-20

## Classification

- **VERIFIED CURRENT STATE:** platform commit
  `29018e69ce893f970d899c5b30631624d8f5d7cf` contains a conditional,
  inactive F3/F4 card and a source-pin test.
- **REPOSITORY INTENT:** F3 may create one retained archive-integrity receipt
  only after a successful October 21 F2 result; F4 may later create one fresh
  non-isolating pre-acquire envelope.
- **UNKNOWN / REQUIRES VERIFICATION:** October 21 F2 has not run, no receipt
  exists, and no F3 or F4 effect has been authorized.

## Independent result

Stream A extracted the exact platform commit into an isolated temporary tree
and ran its focused card suite. Both tests passed. The card SHA-256 is
`3d8c88bd8f4f003efbc0fb9d57ba327153a1fcc4373e42bfdeed7b124ad01467`.
The test pins at least 18 source paths and confirms that the card retains:

- a prerequisite of exactly three valid F2 archive rows with `test_exit=0`;
- unchanged double-read terminal state;
- distinct F3 and F4 approvals;
- an effect-disabled retained producer before F3 release;
- `consumers_isolated=false` and `scheduled_work_quiesced=false` for F4; and
- no automatic retry.

F3 and F4 should remain separate. F3 writes durable evidence from the
completed archive cycle. F4 has a shorter freshness requirement and binds a
later live production observation immediately before the remaining preflight
and recovery gates. Combining them would make Jason approve a future runtime
observation before it exists.

## Decision

The conditional sequence is suitable preparation. It grants no authority and
does not close F2, F3 or F4. If F2 succeeds, the next approval request can be
the already-bounded F3 one-shot receipt creation. If F2 is no-go or uncertain,
neither F3 nor F4 may run.
