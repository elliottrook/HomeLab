# M3 outcome status/verification boundary — 2026-10-22

## Finding

The offline `Outcome` contract allowed a failed, denied, expired, cancelled or
budget-exceeded attempt to claim `fixture-conformance`, and allowed a completed
attempt to claim `not-executed`. Those combinations are semantically
contradictory and could make later routing evidence appear stronger or weaker
than the actual attempt.

## Correction

The contract now permits `fixture-conformance` exactly when status is
`completed`. Every non-completed terminal status must use `not-executed`.
This is a validation boundary only; it adds no route, provider, permission,
confidence score or promotion authority.

## Verification

The isolated Decision and Outcome semantic tests plus the evidence-lineage and
paired-evidence suites passed 14/14. The new test accepts the completed pair and
all five non-completed status pairs, and rejects the six contradictory forms.
The broader historical adapter portion remains deliberately fail-closed on its
reviewed source pin drift; that source definition was not repinned to make this
contract change pass.

## Consequence

Future M3 evidence cannot represent an unverified terminal attempt as
fixture-conformant. Automatic routing remains disabled. Representative
independent labels, calibrated abstention, live shadow comparison and
class-specific latency budgets remain open.
