# SA4 corrected postcheck-lineage inactive install — 2026-11-06

**Result: PASS — installed inactive; no repair authority or effect.**

All eight reviewed files were installed create-exclusive in LXC104. Each is an
exact root-owned, mode-0644, one-link regular file. Installed-path validation
proved the 85-byte healthy v2 artifact passes its byte, metadata and consumer
checks, registry v3 pins those exact installed program hashes, and the bounded
observer/registry graph restores its predecessor bindings.

The v7 runner imported the corrected graph and rejected one unexpected argument
before input. All fresh v4 transaction paths remain absent. The complete v2 and
v3 failed-attempt evidence remains retained, the canary remains
`a9831e62…4da0`, the lease is exactly `ready`, and production is healthy. No
signer, authority, runner attempt, checkpoint, repair, restart, service action,
model change, route or promotion occurred.
