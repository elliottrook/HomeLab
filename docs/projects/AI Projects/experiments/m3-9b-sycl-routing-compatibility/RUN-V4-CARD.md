# M3 9B/SYCL synthetic routing contract v4

> Frozen and executed on 2026-10-12. One versioned development run,
> 30 serial requests, no retry per case. See [result](RESULT-V4-2026-10-12.md).

**Hypothesis:** the v3 mismatch arose because the prompt and JSON schema did
not say that `clarify` or `abstain` must have an empty capability array. v4
adds exactly that instruction and says an unambiguous request with required
capabilities should use `plan`. It leaves the fixed 30-case synthetic fixture,
capability vocabulary, parser, response schema, model, 256-token cap, no-tool
boundary and service identity unchanged. This is deliberate development
iteration on **exposed examples**, never a holdout or calibrated routing
estimate. v1 and its two diagnostics remain separate failed results.

Preflight: nine local mocked tests, exact source/fixture hashes, healthy
inference service, no active competing lab work, zero processing/deferred
requests, existing local service-account key path, and Jason's authorization
to use the mostly idle B60 now. Execute through SSH stdin as `ollama`; never
print or export the key. Output only case IDs, allowed route fields, timing and
failure categories. No raw prompt or model text, no tools, no new permission,
no runtime setting change.

Run in file order, one attempt per case, maximum 30 calls or 20 minutes, with
a 90-second per-request timeout. Stop on the first invalid/HTTP/transport
result or service degradation. Report complete-case count, exact-match count,
extra/missing capabilities and p50/p95 only after 30 valid responses. A 30/30
schema-valid result is sufficient to propose a **separate** representative
evaluation; it does not activate a router. Any early failure rejects v4's
interface and ends this session's compatibility series. Keep the accepted
runtime; no rollback is needed beyond ending calls and verifying health.
