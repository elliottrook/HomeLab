# D4 strict JSON number boundary — 2026-10-23

## Finding and correction

The fresh investigation executor rejected repeated JSON keys and later checked
finite result metadata, but Python's decoder still accepted the non-standard
numeric tokens `NaN`, `Infinity` and `-Infinity`. These tokens are not portable
JSON and could survive parsing in an otherwise unused or not-yet-validated
field.

The common bounded decoder for case, manifest, health and completion data now
rejects every non-JSON numeric constant before typed validation.

## Verification and limit

A normal object decoded successfully. Synthetic objects containing each of
`NaN`, `Infinity` and `-Infinity` were rejected. The complete evaluation unit
suite passed 120/120.

This hardens offline evidence portability and input handling. It does not call
a model, change the production service, qualify an investigation, connect a
tool or grant authority.
