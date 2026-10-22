# D4 investigation freshness vocabulary boundary — 2026-10-22

## Finding

The sealed-package validator already restricted observation freshness to
`current`, `stale` or `unavailable`, but the lower-level investigation engine
accepted any non-empty freshness string. A direct development fixture could
therefore reach the model with an unrecognised freshness claim even though the
same record would be rejected by the package boundary.

## Correction

The investigation engine now applies the same closed freshness vocabulary to
initial and simulated check observations before constructing any model request.
Malformed freshness fails before transport. This keeps freshness as typed data
rather than free text and makes the engine and package boundaries consistent.

## Verification and limit

A new test supplies an unrecognised freshness value, confirms validation fails,
and confirms transport is never called. The complete eval unit suite passed
111/111. This is offline schema hardening only: it does not call or qualify a
model, authenticate an evidence producer, connect a tool, grant authority or
advance M1.
