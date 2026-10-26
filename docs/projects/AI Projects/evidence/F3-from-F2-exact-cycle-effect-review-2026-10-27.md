# F3-from-F2 exact-cycle effect review — 2026-10-27

**Decision:** GO for one separately approved conditional F3 conversion after a
complete, independently reconciled October 27 F2 result.

The platform source card is commit
`35b5f61d80fdc65a3cde17751eedcfe94ac6093b`. Card SHA-256 is
`d89429cca8571cb77a208a4b9845e5a6385257d7754be79b4e875a1b18149fd5`;
its focused test SHA-256 is
`809d7f153a7e285c86d6ef9a5f91ceae82257b678fd6be5ea369b4660d3f0e7e`.

## Review result

- The card binds only cycle `2026-10-27` and requires the exact root-custodied
  successful F2 state with three exit-zero rows.
- It pins the corrected installed F2 coordinator at `6a1d520a…8193` and the
  exact installed converter, adapter and verifier identities.
- All four target files match the card as `root:root 0644`, regular, one-link
  files. The retained receipt is absent, its parent is `root:root 0700`, and
  the lease is ready with no lease or lock.
- The focused new card tests pass 3/3. The complete F3-from-F2 suite passes
  14/14 after historical October 25/26 card tests were corrected to validate
  their frozen historical pins rather than the moving current source.
- The one permitted effect invokes the installed converter once, writes no
  archive data and performs no archive rescan. Any missing, stale, changed,
  partial, NO-GO or uncertain evidence refuses the effect without retry.
- F4 must use a later fresh backup cycle; F5/F6, consumer stops and model calls
  remain blocked.

The card and review do not authorize the conversion. A conditional exact-cycle
effect approval and one occurrence after the 01:42 F2 reconciliation are still
required. A failed or uncertain F2 result must skip F3 and write nothing.
