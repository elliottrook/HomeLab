# SA4 fixed-runner inactive-install review — 2026-11-06

Fresh checks found the runner destination absent, both installed LXC
dependencies exact, runtime controls/exchange absent and the whole-host lease
ready. The one-file plan creates only runner `d48e26d5…b74e` as a root-owned
mode-`0644` file. Rollback removes it only while its exact hash still matches.

Postchecks hash, inspect and import only; they cannot create inputs, ledger or
runtime state, invoke the runner or signer, or touch the target/services. Three
focused tests and the full 201-test SA4 suite pass. Installation is the next
explicit deployment gate; no repair is authorized.

The independent result verifier is also source-complete and rejects runner,
authority, target or metadata drift. The expanded suite passes 204/204. Offline
preparation for this deployment gate is exhausted.
