# M3 9B/SYCL response-shape diagnostic v2

> Frozen before execution on 2026-10-12. One diagnostic call only, using
> `timer-cal` from the same pinned synthetic development fixture. This is a
> new case, not a retry or rescore of v1's `timer-train`.

**Hypothesis:** v1's first `invalid_response` came from either non-JSON model
content, an unexpected JSON shape/capability, or an incomplete response. The
v1 record cannot distinguish them because it intentionally discarded raw
text. v2 keeps the same system message, schema constraint, model, request cap
and no-tool boundary but records only the response's finish class, content
type/byte count/SHA-256, JSON type, expected-key presence, extra-key count and
the first failed parse stage. It never prints the raw response, request text,
API key or arbitrary JSON keys.

The case is `timer-cal` (“Create a five minute countdown timer”), fixture
SHA-256 `c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec`.
Exactly one request, no retry, 90-second network timeout and 256 generated
tokens maximum. Execute as the existing `ollama` account with the existing
local key file via SSH stdin. Recheck service health, slot occupancy and any
competing lab work first. Stop after this one response regardless of result;
no production setting or permission changes. If unsafe or interrupted, retain
the partial code/result and stop. Seven offline tests, including content/key
exclusion, passed before execution.

Success here means **diagnostic clarity**, not model qualification. A valid
response on this different case would not erase v1's failure. A JSON syntax,
schema, content-type or truncation result should lead to one explicit
interface hypothesis and a separate versioned experiment; it should not be
silently patched into v1. The frozen S1 human holdout remains untouched.
