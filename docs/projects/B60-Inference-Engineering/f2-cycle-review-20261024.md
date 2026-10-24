# October 24 F2 terminal observation — NO-GO

Nightly heartbeat timestamp 09:07:38 UTC (02:07:38 PDT); first execution
clock 09:18:28 UTC (02:18:28 PDT). Fresh Forgejo fetches leave Adaptive at
`cf5cfaf342470bcdbfae06eda4339f3f89977a44`, platform at
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`, compatibility at
`1dd38c762e7598646a94d49cc44188376d6952ea`, and published B60 at
`e58ed7c04cb187971854509757644ee0f6b09381`.

Adaptive's approved activation result
`docs/projects/AI Projects/evidence/F2-exact-cycle-activation-result-2026-10-24.md`
still hashes to
`862247b866c41e96f8de0bd3693f032437362726c25ccf17a600615c85cffe8e`.
There is not yet a newer published terminal outcome on the fetched refs.

## Direct bounded observation

Before the probes, the documented lease paths were absent and no kernel lock
matched the state-directory identity. This is a point-in-time observation,
not a continuing exclusion or an experiment admission.

The protected, bounded October 24 scheduled-state projection reports:

- schema `aster-f2-scheduled.v1`, cycle `2026-10-24`;
- phase `final`, state `no_go`, first failure phase `final`;
- failure/error class `FINAL_GUARD_SUBCHECK_FAILED`;
- no `result` field. No successful archive result is available here.

Systemd reports prepare 01:15:00–01:15:05 PDT, status 0/success; final
01:20:00–01:20:01 PDT, status 1/failed. Both exact-date timer units are now
not-found/inactive with no next elapse. B60 did not remove or stop them and
does not infer who completed cleanup. No scan or guard was invoked by B60.

This proves a final-guard refusal, not archive corruption or a GPU failure.
The generic code does not identify the original failing subcheck. It must not
be relabelled as a successful F2 or retried under the consumed cycle.

## Static installed-source review (not execution)

Current fixed module identities observed via hashing and AST-only extraction:

| Module | SHA-256 |
|---|---|
| `f2_preflight_snapshot.py` | `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684` |
| `f2_scheduled_release_candidate.py` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` |
| `f2_preflight_fixed_wrapper.py` | `0dbdbce56be6f72ada8df54dd28cfcda32f6494200ba97f4b40703496271ba9f` |

Snapshot/coordinator mtime epochs are respectively 1792850294.3421495 and
1792850294.3439138. Current bytes differ from the last published Adaptive
installation receipt; they are not proof of exactly which bytes ran earlier.
Do not overwrite these newer files with an older B60 proposal.

The current coordinator still declares `final(..., popen=subprocess.run, ...)`
and subsequently consumes `process.communicate()`, `process.pid` and
`process.returncode`. That remains a concrete process-interface defect, but
it is **not today's observed cause**: final-guard processing precedes launch.
The generic failure path wraps exceptions other than its typed guard exception;
the wrapper reads the fixed snapshot, acquires its coordinator context and
calls `final_guard`. Current snapshot source has typed codes for individual
guard failures. Without retained bounded evidence for the untyped wrapper
failure, naming a specific failed check would be speculation.

One static-source extractor failed on its own undefined variable before
reading the requested functions; a corrected read-only extractor succeeded.
One terminal projection query stalled and was retried once; that was a read
retry only, never a scan retry. No raw log, model output, private corpus or
credential value was accessed.

## Owner action and B60 continuation

Publish the current source/install ancestry and exact cycle provenance. Split
the remaining generic wrapper failure into fixed, bounded codes for snapshot
read/custody, exclusion entry and typed final checks without exposing arbitrary
exceptions. Review/test those paths offline and on target Linux. Correct the
launcher default with a default-path process-contract test before another
approved cycle can reach it. Keep timing, backup, exclusion and recovery gates
intact; do not drop a gate to get a pass.

F2 remains NO-GO; F3/F4, live recovery and the separate A1 benchmark remain
unadmitted. Eighty-one B60 offline tests pass, not new owner-source tests or
live recovery proof. No model, GPU, lease, production service/timer, schedule,
credential, download, mount or configuration mutation occurred. No push in
this nightly turn; retain this focused record for the next authorized liaison
continuation. No full production-health validation is claimed from these probes.
