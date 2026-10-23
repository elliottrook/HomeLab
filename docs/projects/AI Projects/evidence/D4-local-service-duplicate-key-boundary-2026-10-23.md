# D4 local-service duplicate-key boundary — 2026-10-23

## Finding and correction

The fresh investigation executor bounded local inference responses before JSON
decoding, but the default decoder accepted repeated object keys by keeping only
the last value. A malformed health or completion response could therefore make
an earlier status or answer field invisible before the typed response checks.

Health and completion responses now use the same repeated-key rejection as the
bounded case and manifest inputs. The response byte envelope, redirect denial,
direct local transport and downstream answer sanitizer remain in place.

## Verification and limit

A normal synthetic service object decoded successfully and a repeated-key
object was rejected. The complete evaluation unit suite passed 120/120.

This closes an offline parsing ambiguity. It does not call a model, change the
production service, qualify an investigation, connect a tool or grant
authority.
