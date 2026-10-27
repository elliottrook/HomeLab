# Full-Aster private capture boundary — 2026-10-26

## Result

**PASS for source-only capture validation. No model run is authorized.**

The matched benchmark now has a strict private capture schema for each model
role. It binds the exact owner-frozen packet, role-specific model/runtime/mode
and all 24 ordered cases. Each completed row contains only the answer and
bounded end-to-end, first-token, token-count and memory observations. Hidden
reasoning is excluded.

The validator enforces zero retries and stops the remaining batch after the
first timeout, failure or uncertain result. A content-free manifest exposes
only the capture digest, byte count and status totals. It never exports answer
text. Model output remains `authority: not-granted`.

Focused tests cover complete capture, model/packet drift, forbidden reasoning
retention, malformed timing and attempted work after a terminal failure.

This closes the result-format gap only. The owner packet and final contract
must still be frozen, the two-request challenger screen must pass within fresh
F2–F6 admission, and a separate exact live approval must precede the 48-call
matched run. No lease, service change, restart, model request, routing change
or remote write occurred.
