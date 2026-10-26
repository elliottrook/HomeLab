# Stream A F4/F5 admission and candidate-H inactive installation result

Status: **PASS — INACTIVE SOURCE COMPATIBILITY ONLY**

Jason approved the exact four-file inactive installation on 2026-10-25. The
installed source is local commit `f109c1f0`, which independently passed source
review after correcting the artifact-size bound and pinning the accepted F5
binary, unit and authentication identities.

## Installed identities

| Target | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_admission.py` | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` | `root:root 0644`, regular, one link |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | `3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7` | `root:root 0644`, regular, one link |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0` | `root:root 0644`, regular, one link |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | `d3c8924e4e1cb5165d70ca36a4fc335b465445d1881390a8ba7c83ab44a508ed` | `root:root 0644`, regular, one link |

The three replaced files are preserved byte-for-byte under root-owned mode
`0700` checkpoint directory
`/var/lib/local-ai-lab/checkpoints/stream-a-admission-f109c1f0-20261025`.
Their hashes match the install card's measured prestate. The checkpoint also
records that the admission library was absent before this transaction.

## Validation

- Installed-path imports passed with bytecode writing disabled.
- The admission, lease, adapter, entrypoint and watchdog suites passed 69/69
  on target Linux.
- The isolated real-wrapper test passed 1/1 after constructing its required
  repository-shaped temporary fixture. The first test invocation had omitted
  fixture source files and therefore produced a staging error; it did not
  identify an installed-source failure or invoke an effect.
- The unchanged wrapper returned only
  `{"effects":"disabled","state":"source-only"}` without creating bytecode.
- Both watchdog and owner-heartbeat timers remained disabled and inactive.
- No evaluation lease, lease lock, operation lock, F5 observation, admission
  artifact, evaluation process or candidate-H workload existed after the
  transaction.

This result does not produce F4/F5 evidence, arm F6 recovery, acquire a lease,
stop a consumer, call a model, start candidate H or M3, or authorize the
effectful run. The next serial gate is a reviewed fixed-source F5 observation
and canonical admission-production transaction for an eligible cycle.
