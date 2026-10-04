# SA3 Doctor observation — existing workflow failure

Status: **observed; no acceptance result**  
Date: 2026-10-03  
Classification: **VERIFIED CURRENT STATE** for the bounded execution record;
**ARCHITECTURAL INFERENCE** where labelled.

## What was requested

One authenticated Doctor request was sent through the existing Aster interface
under the approved read-only pilot boundary.

## Verified execution record

- The dedicated Stream A incident adapter was disabled by its feature flag and
  did not handle the request.
- The pre-existing Lab Operations Doctor route accepted and claimed one job.
- The fixed Doctor script started through the Mac outbound worker; it had no
  arbitrary command input and no remediation capability.
- The job reached terminal state `unknown`, code `interrupted`, with
  `coverage: none` and zero recorded checks.
- The worker's private operation log existed, but contained none of the three
  required aggregate markers (`Passed`, `Warnings`, `Failed`). Its parser could
  therefore not construct an evidence result and failed closed.
- No automatic retry or compensating action was started.

## Interpretation

**ARCHITECTURAL INFERENCE:** the existing Doctor script's current output
contract is incompatible with the deployed Lab Operations parser, or the
script ended before emitting its expected summary. Either explanation is
sufficient to reject this run as diagnostic evidence. The safe terminal state
is the correct outcome for an incomplete observation, but it leaves the
requested health check unresolved.

## Decision

Do not infer lab health; do not retry automatically; do not enable the Stream A
adapter merely to mask this failure. Before another Doctor execution, create a
small, separately reviewed compatibility investigation that reads the fixed
private operation log, identifies the missing output contract, and validates a
parser/script repair using a recorded fixture. Any live deployment remains a
separate approval boundary.

## Learning-plane value

This run is retained as a negative integration example: an allowed route,
worker, and script can still fail at the evidence-contract boundary. It should
be labelled `outcome_unavailable`, not `health_failure`, and excluded from any
routing-success calculation.
