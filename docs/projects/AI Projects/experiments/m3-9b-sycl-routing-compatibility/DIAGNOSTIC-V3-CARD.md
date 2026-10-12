# M3 9B/SYCL value-contract diagnostic v3

> Frozen before execution on 2026-10-12. One call only on the new synthetic
> `timer-test` case. Do not retry either earlier timer case.

The v2 response was complete, JSON, and had exactly `status` and
`capabilities`, yet failed validation. This v3 diagnostic uses the same
no-tool request, model, schema constraint, 256-token response cap and
90-second timeout. It records only the two value types, whether status is
allowed, number of capabilities, and counts of non-string, unknown and
duplicate IDs or non-plan capabilities. It does not emit actual unexpected
values, raw response, prompt or service key. A SHA-256 of the content supports
provenance without retaining text. The pinned fixture remains
`c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec`.

The hypothesis is that v2 failed an enum/type or allowed-ID rule, rather than
transport, JSON syntax or extra fields. Eight local mocked tests, including
exclusion of unknown values, must pass before the call. Recheck health and
zero processing/deferred requests. Stop after this call regardless of result;
there is no 30-case rerun under this card. The result can guide a later
versioned interface change, but cannot establish routing quality, confidence
or authority.
