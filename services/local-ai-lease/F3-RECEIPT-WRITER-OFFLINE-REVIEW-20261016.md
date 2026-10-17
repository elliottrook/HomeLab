# F3 receipt writer — offline custody review

**Status:** source-only candidate; F3 remains HOLD. No host file, timer,
receipt, lease, backup or running service changed.

The candidate source-receipt writer previously called `mkdir(...,
exist_ok=True)`, wrote through a predictable `<receipt>.new` path, replaced
the destination, and checked root-only directory/file custody only afterward.
If the parent was already unsafe or that temporary name was a symlink, the
check came too late to prevent the write. This was a source-level risk, not
evidence of a live incident or of an enabled F3 path.

The offline candidate now requires a root-owned mode-0700 directory before
opening a temporary file, rejects an unsafe existing receipt, writes to a
unique mode-0600 temporary file, flushes the file and directory, and then
rechecks final custody. An interrupted replacement leaves the previous
receipt in place and cleans up its unique temporary file. A failure after
replacement must still be treated as an uncertain outcome and reconciled;
it must not trigger an automatic retry.

Pinned source SHA-256:

- `scripts/local-ai/source_receipt_boundary.py`:
  `84a5b684030d288afe02273a525e3d04c8a67e7c8aa7d426d74526ec09eb3dd1`
- `scripts/local-ai/test_source_receipt_boundary.py`:
  `ba75b64e10b38566af7d01fb4398a817d8256dde45a6576ed6736846de2407ce`

The focused `test_source_receipt_boundary`, `test_source_receipts` and
`test_fixed_source_adapters` suites passed 17 tests on macOS, with two
root-custody cases skipped because this process is not root. New negative
cases prove an unsafe parent is rejected before writing and a pre-existing
predictable `.new` symlink is not used; a synthetic replacement failure leaves
the old receipt intact. **Target-Linux root-custody and failure-path proof is
still required** before any F3 release review.

The current source `produce_candidate_receipt()` calls
`FixedSourceAdapters.evidence_from_retained()`; the platform full-stop run
card's statement that this source path still calls `evidence()` is stale.
This is a documentation correction to verify against the eventual installed
bytes, not proof that the retained receipt path is live. The platform owner
has been notified. F2 timing, separate F3 effect-enabled source review,
fresh-cycle receipt, F6 recovery and human drill approval remain independent
gates.
