# SA4 distinct canary v2 seed-install result — 2026-11-06

Jason approved the exact two-file inactive installation. Fresh preflight found
both destinations absent, the installed v1 registry exact, the original canary
healthy, the spent v6 ledger unchanged, runtime controls absent, the lease
ready and bounded production healthy.

The accepted v2 registry and 85-byte drifted inert seed were staged with exact
hashes, linked create-exclusively into their fixed LXC104 destinations and
then reduced to one link each. Both are root-owned, root-grouped mode-0644
regular files. An isolated import proved that v2 resolves both targets while
v1 still rejects the new target ID.

Independent postcheck found exact hashes `86c44272…a39` and
`a9831e62…4da0`, unchanged v1 registry `0091a90f…9d83`, unchanged healthy
original canary `4529dee5…1065`, unchanged terminal v6 ledger
`f7dde1e0…3c1c`, absent runtime state and no SA4 runner or signer. The lease is
`ready`; LXC104/110/116, Aster Agent, llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are healthy. No service action, restart,
authority, ledger transition, repair, route or promotion occurred.

The canonical result beside this record passes the strict source validator.
Rollback remains exact removal of the seed followed by the inactive registry.
Next is source-only integration of the accepted registry into a new fixed v3
transaction chain, its inactive installation review and zero-effect preflight.
No repair is currently authorized.
