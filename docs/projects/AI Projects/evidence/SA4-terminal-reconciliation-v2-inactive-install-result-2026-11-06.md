# SA4 terminal reconciliation v2 inactive-install result — 2026-11-06

Jason approved the exact four-file create-only installation. Fresh preflight
found all destinations absent, both installed v1 dependency hashes exact, the
spent v6 ledger and healthy canary unchanged, runtime controls absent, the
whole-host lease ready and bounded production healthy.

All four v2 files were staged with exact hashes and linked create-exclusively
into their fixed LXC104 destinations. After verified installation, staging
links were removed. Each destination is now a root-owned, root-grouped,
mode-0644 regular file with one link. Isolated imports passed with bytecode
writes disabled.

Independent postcheck found the exact four hashes, exact v1 dependencies,
unchanged canary `4529dee5…1065`, unchanged terminal uncertain ledger record
`f7dde1e0…3c1c`, absent operation lock/emergency stop/observer exchange, no v2
process, lease `ready`, running LXC104/110/116 and healthy Aster Agent,
llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd`. No runner, signer,
authority, ledger rewrite, target effect, service action, restart, route or
promotion occurred.

The canonical result is retained beside this record and passes the strict
source validator. Rollback remains exact removal of these four after-hash
files. The installed v2 chain remains inert. Next is installed-path
zero-effect validation and the design/review of a distinct inert canary; the
repaired v6 canary and burned grant are not reused.
