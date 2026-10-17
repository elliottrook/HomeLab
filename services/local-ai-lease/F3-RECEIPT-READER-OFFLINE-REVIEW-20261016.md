# F3 receipt reader — offline shape and custody review

**Status:** source-only candidate. F3 remains HOLD; no host installation,
receipt, lease or live backup check occurred.

The earlier reader checked path custody before opening but did not check the
opened file descriptor. It parsed an unbounded JSON file and allowed malformed
field types such as a boolean generation or numeric `backup_verified` value
to reach the permissive candidate evidence shape guard. Such data failed in
some cases by incidental exception, but was not consistently rejected by the
receipt contract. This review makes the reader deny malformed or oversized
evidence explicitly; it does not claim a live tampering incident.

The candidate now validates a root-owned mode-0700 parent and the opened
regular file's owner, mode, single link and 8192-byte size bound. It reads at
most 8193 bytes, requires the exact receipt and evidence field sets and exact
integer/boolean/list types, then applies the existing candidate admission
shape check. The writer shares the size limit and retains the previously
reviewed unique-temporary-file and fsync behavior. An unreadable or invalid
receipt is a denial, never a reason to retry a prior uncertain write.

Pinned source SHA-256:

- `scripts/local-ai/source_receipt_boundary.py`:
  `033a21f798536dcc53f9ffcdf6589ff9725067976f4d146b2da142d3530fa784`
- `scripts/local-ai/test_source_receipt_boundary.py`:
  `ced83f24f3fa136fabecf1bba2f06c946178f907d979fedc8778234da0fa888f`

The focused source-receipt/adapter suites passed 18 tests, with two
root-custody cases skipped on macOS. The full `scripts/local-ai` offline
suite passed 209 tests with the same two skips. New cases cover malformed
top-level and evidence fields, boolean-as-integer generation/timestamp and
numeric-as-boolean evidence. **Target-Linux root-custody, stale/oversized
file, and actual installed-path tests remain required before release.**

The source-only `produce_candidate_receipt()` still uses
`evidence_from_retained()` and checks that its backup digest matches the
acquired lease. The F2 observation cannot supply a trusted F3 receipt.
Independent review, F2 timing assessment, effect-enabled source, one-cycle
approval, installed-path rollback and fresh-cycle receipt proof remain open.
