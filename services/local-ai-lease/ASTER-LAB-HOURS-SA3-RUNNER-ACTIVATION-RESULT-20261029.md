# SA3 reserved-runner activation result — 2026-10-29

Status: **PASS — runner available; no booking or execution created**

The first `v1` installation stopped before checkpoint or target write because
its source validator incorrectly required staged repository files to have their
eventual executable target modes. The failed stage was retained and was not
retried. Production was unchanged.

Corrected candidate `v2` passed 53/53 focused tests and two byte-identical
bundle builds at SHA-256
`5f4a50d4cbae3021775756b3754ec7226047775df9e5e02cccc106fb30b0fc12`.
It independently validates source custody and applies pinned target modes only
during atomic installation under fresh checkpoint `sa3-runner-activation-v2`.

The live installer returned `state=installed-inactive`, `files=3`,
`sa3_runner=available`, `effects=not-attempted` and retained the rollback
checkpoint. Independent postcheck verified:

- full-drain runtime `3026a792bcc1375b98d537680f4f2ff2ee00aeb0e8590498337f8e680d6d8279` mode 0755;
- reserved runner `8d222d538e3ffc201cb0a7a29e06a69bf808fe3b6ba7d5c9283a5e26170402bb` mode 0755;
- release manifest `7c28fb4a6eb439b7a9fbdc79b48298b5740fae07ee26fc7b963adcb4a0aa67b9` mode 0644;
- all eighteen manifest pins;
- the generated owner transaction binds the fixed SA3 profile and booking-specific root-only result directory;
- no SA3 booking or attempt exists;
- LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech and Proxmox daemons remain healthy; and
- the local AI lease remains exactly ready.

The next step is a checked Lab Hours reservation and one bounded evaluation.
It still requires a conflict-free authoritative ledger result, the fixed
reservation, whole-host lease and shared operation lock at runtime. No model,
service, timer, schedule or restart was touched by this installation.
