# October 26 F2 communication failure: default-path reproduction

## Fresh receipt and bounded observation

Fetched Adaptive `99efcf2e119099aa3ed2b9b7537bee4fd553bca7`, platform
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`, and published B60
`69f302a198615260c40e5228da8a551ec686e25a`. No October 26 terminal result
is yet published on those refs. The independently received pre-effect recovery
receipt remains SHA-256 `fc8ee5dedbb6a926f478d9cdfe6b2f18c58c58c3b25c79a2074e3ec05a14a17b`;
that exercise does not qualify a production workload.

A read-only state-directory lock/lease-path observation found no match. This
is not continuing exclusion or experiment admission. A root-owned, regular,
bounded terminal projection then reported:

- schema `aster-f2-scheduled.v1`, cycle `2026-10-26`, phase `final`;
- state `no_go`, first failure phase `final`;
- failure class `OBSERVER_COMMUNICATION_FAILED`, no `result` field.

Systemd reports prepare 01:15:00–01:15:05 PDT, exit 0; final
01:20:00–01:20:05 PDT, exit 1. Exact-date timers are not-found/inactive with
no next elapse. B60 did not stop/remove them or infer who reconciled them.
No archive or scanner was invoked or retried by B60. An observer child may
have run before communication failed; no successful integrity result was
retained here. Do not claim the scanner never started or that archives passed.

## Concrete process-contract defect

The current installed coordinator is still SHA-256
`9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1`,
mtime epoch 1792850294.3439138. Static AST inspection confirms the CLI calls
`final(runner)` with no process-factory override. Its default is
`popen=subprocess.run`, but the function subsequently calls `.communicate()`
and accesses `.pid` as though it received a `Popen` handle. `run` instead
returns a `CompletedProcess`, which has no `.communicate()`.

This is the concrete default-path defect B60 reported October 20 and again
October 24. It deterministically produces the currently observed bounded
communication code under that default, regardless of a child return code.
The retained class alone is not an exception traceback or proof of the child's
outcome; do not invent either. Current static source is not an execution-time
hash receipt, though it matches B60's earlier observed module identity.

## Exact offline reproducer and minimum logical correction

Copied only the static `final` function after the remote reader verified the
entire source-module hash above. The fixture is not a deployable controller.
Its local source/test files are:

- `scripts/b60-inference/review-fixtures/final_fixture.py`, SHA-256
  `511c903b4393213f0852f1cee6fc8e8cf68656db9cd2deaa5da60da7730a7bdf`;
- `scripts/b60-inference/review-fixtures/test_default_contract.py`, SHA-256
  `f494bd27fad8cbd2d73236f893a38b1d6dce3f6449ee18d4b5819952d4126af1`.

Run from that review-fixtures directory:

`python3 -m unittest test_default_contract`

**2/2 pass:** the original default reproduces `OBSERVER_COMMUNICATION_FAILED`
with `AttributeError` as its cause; an AST-only change of the default to a
fake `Popen` handle reaches synthetic completion. All host, clock, guard,
process, persistence and projection boundaries are fake. No child process,
network, credential, actual archive or GPU is used. The synthetic success is
not a passed guard, archive check, recovery or qualification.

Minimum logical patch, for owner review only:

```diff
-def final(runner: Callable, *, popen=subprocess.run,
+def final(runner: Callable, *, popen=subprocess.Popen,
```

## Exact next owner action, to avoid another blind overnight attempt

Publish the current platform source ancestry. Integrate the factory correction
with a default-path regression, not only tests that inject a Popen-like fake.
Review and update the **entire pin dependency closure** for the changed module;
the one-line logical correction does not imply a one-file safe installation.
Verify every fixed wrapper/observer/producer expected hash against the complete
candidate packet before scheduling. Preserve first-failure codes and no-retry
semantics, prove target-Linux import/process-interface/timeout behavior and
retain an exact rollback checkpoint. Do not replay the consumed cycle or drop
a freshness, backup, exclusion or identity check to get a pass.

This preparation heartbeat grants no host-change or scan authority. F2 remains
NO-GO; F3–F5, effectful recovery and A1/B60 model admission stay closed.
No full production-health check is inferred from the helper-unit observations.
No model/GPU call, lease, service/timer/configuration, package, credential,
mount or download mutation occurred. Publish this focused source/test evidence
on the standing-authorized liaison branch; delivery still requires a peer
receipt rather than inference from the push.
