# D4 local credential proxy boundary — 2026-10-23

## Finding and correction

The fresh investigation executor pins its inference target to the accepted
private address and rejects HTTP redirects, but its URL opener still inherited
proxy settings from the invoking environment. A stray `HTTP_PROXY` setting
could therefore send the local-service request and bearer credential to an
unintended proxy instead of directly to the fixed LAN endpoint.

The executor now constructs its opener with an explicitly empty proxy handler
before adding the no-redirect policy. Health, metrics and completion requests
therefore use direct transport even if the invoking environment defines a
proxy.

## Verification and limit

The focused test supplied a synthetic `HTTP_PROXY` value and verified that the
resulting opener contains no environment-derived proxy handler. The existing
redirect denial still passes, and the complete evaluation unit suite passed
120/120.

This protects a credential boundary in an offline, separately approved runner.
It does not read a credential now, call a model, change the production service,
qualify an investigation, connect a tool or grant authority.
