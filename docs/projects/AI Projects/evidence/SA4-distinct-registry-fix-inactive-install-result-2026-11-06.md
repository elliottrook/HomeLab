# SA4 distinct-registry correction inactive install — 2026-11-06

**Result: PASS — installed inactive; no repair authority or effect.**

After a fresh exact preflight, three new files were installed create-exclusive
in LXC104. Each is root-owned, mode `0644`, a regular one-link file and matches
its reviewed SHA-256. All 16 installed dependencies, the predecessor result and
the drifted v2 canary matched their fixed identities before installation.

The installed-path regression proved the old validator rejects the distinct
target, the complete v2 binding accepts it, nested runner/owner binding remains
coherent, and every module returns to registry v1 afterward. The final runner
was called once with an unexpected argument and exited `1` with its fixed
fail-before-input error. It did not open transaction inputs or create evidence,
a ledger, lock, emergency-stop state, checkpoint or repair process.

The canary remains `a9831e62…4da0`. The whole-host lease is exactly ready;
LXC104/110/116, Aster Agent, the accepted llama.cpp/SYCL service, Speech,
`pvescheduler` and `pvestatd` are healthy. No service action, restart, model
change, route or promotion occurred. The next step is a fresh source release
and unsigned authority boundary bound to this exact installation result.

