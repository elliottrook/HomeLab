# SA3 inactive registration installation result — 2026-10-29

Status: **PASS — registered inactive; guest validation corrected and passed**

The five-file registration installer returned `state=installed-inactive`,
`files=5`, `effects=not-attempted` and retained its root-only rollback
checkpoint. All exact hashes, modes, owners, single-link custody, eighteen
release-manifest pins and Python imports passed. The fixed identity is twenty
requests, 120 seconds per request, a 2,700-second workload deadline, a
3,600-second minimum booking and a 900-second recovery reserve. Its runner
still returns `WORKLOAD_RUNNER_UNAVAILABLE` before attempt evidence, guardian
arming or production drain.

The first independent target-validator invocation exposed a namespace defect:
it looked for the four evaluation files on Proxmox even though the reviewed
dormant installation correctly placed them in LXC110. The check failed closed;
no booking, lease, attempt, model request or service effect occurred.

Platform correction `4bad2da3` replaces only the validator and release manifest
against their exact installed hashes. Its 29/29 suite and two deterministic
bundle builds passed. The installer returned `state=installed-inactive`,
`files=2`, `guest_validation=pass`, `effects=not-attempted` and retained a
second root-only checkpoint. Independent execution of the installed validator
then returned:

```json
{"effects":"not-attempted","guest":"110","runtime_files":4,"state":"valid","target_units":"absent","workload_id":"sa3-expanded-source-quality-v1"}
```

The installed validator is SHA-256
`fd467544649cc877ca06f831d8f84aaca495416c19072256bd228fc11601ae33` and
the reconciled manifest is
`51a9cd3a450710ad755cf924aef0df6e900edcf6cca2db4cffe054cb2437f74c`.
The target service/timer and attempt evidence remain absent. LXC104/110/116,
Aster Agent, accepted llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd` are
healthy, and the lease remains exactly ready.

This completes inactive registration and validation. It does not authorize a
booking or model execution. The next implementation item is the exact reserved
runner transaction that uses the already installed host transaction, listener
adapter and fixed LXC110 wrapper, then a separately checked and reserved Lab
Hours evaluation window.
