# October 20 F2 outcome and source-only corrections

Decision: F2 remains NO-GO. No model trial, scan retry, lease or production
mutation was performed by B60. This is preparation-only observation and
offline review, not adoption of another owner's release authority.

## Exact owner receipt and live outcome

Fetched Adaptive `a2cae9e3e9354f20308f356e1487a0c0bc8be665`, platform
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`, and B60
`ea0a5818acc14a9e0cecd1b83d2424bcd8523b50`. The platform advance since
442c0c00 is printer-only; no new F2 result was published on these refs.

After observing no matching state-directory kernel lock or documented lease
paths, read only the protected terminal projection and systemd result fields:

- Prepare ran October 20 01:09:00–01:09:05 PDT, exit 1, failed.
- Final ran 01:10:00–01:10:00 PDT, exit 1, failed.
- `/var/lib/local-ai-lab/f2-scheduled/2026-10-20.json` was root-owned mode
  0600, bounded to 16 KiB, schema `aster-f2-scheduled.v1`, phase `final`,
  state `no_go`, error class `ScheduledF2Error`, zero retained archive rows.
- Both October 20 exact-date timers are disabled/inactive with no next elapse.
  B60 did not disable them or infer which owner performed cleanup.
- The fixed preflight `current.json` was absent when later checked.

This proves on-time service dispatch and a preflight/final refusal, not a
failed `zstd` integrity test, an admitted scan or healthy production validation.
The final class does not identify the original five-second preparation cause.
No raw task output, credentials or private corpus was read. Directory-lock
absence is a snapshot, not continuing exclusion or admission.

## Offline reproductions and minimum launcher correction

Reviewed platform source at exact 6fb0207f:

- `scripts/local-ai/f2_scheduled_release_candidate.py` SHA-256
  `67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d`.
- `scripts/local-ai/f2_preflight_snapshot.py` SHA-256
  `a2324d6a5ba4869778713319a511acc207f1d8332dd1af7e4520be382cfe02fa`.

Four B60 diagnostics pass **by reproducing findings**, not by proving a fix:

1. `final()` defaults its process factory to blocking `subprocess.run`, but
   consumes a `Popen` interface (`communicate`, `pid`). A fake CompletedProcess
   reproduces AttributeError after an otherwise valid synthetic final gate.
   Existing tests inject fake Popen-like objects and miss that default.
2. Before task 3 has run, a fixture with task 1 successful but no new LXC110
   mirror is rejected by `collect_snapshot()`. The owner's early-task test
   supplies a current mirror even while task 3 has no result. A current mirror
   at 01:09 is not guaranteed by its documented 02:00 task. This is a
   source-level prerequisite/timing conflict, **not proved as today's cause**.
3. The pinned coordinator overwrites a preparation failure with the final
   `ScheduledF2Error`, losing the original failure class in terminal state.

The smallest launcher proposal changes only:

```diff
-def final(runner: Callable, *, popen=subprocess.run,
+def final(runner: Callable, *, popen=subprocess.Popen,
```

Applied only to a disposable exact-peer source extraction: eight owner
coordinator tests pass, plus a default-factory identity assertion; no child
process was launched. Resulting candidate SHA-256 is
`cea91ccae41cf1c46f2f9eecd575a866d3ed4658a2132c6f14b84ec87e3e5501`.
That full-file hash is for the old peer snapshot, **not an install candidate
over newer host bytes**. 81 B60 inference tests also pass separately.

Reproduce the four original-source diagnostics with
`scripts/b60-inference/review-fixtures/f2_peer_diagnostics.py`, supplying an
exact unmodified platform `scripts/local-ai` extraction. It checks the pinned
coordinator hash and uses only fake transports/processes and disposable files.
Do not run it against production or call it an archive/recovery test.

## New live source drift and requested owner reconciliation

A later read-only installed-byte check found the coordinator now hashes to
`fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356`,
mtime October 20 10:16:00 PDT, not the published pin. Its signature still
defaults to `subprocess.run`; bounded body inspection still consumes
`process.communicate()` and `process.pid`. It now calls `_record_failure`,
so do not assume the historical terminal-overwrite finding is still unfixed
in those newer bytes. The installed snapshot module still matches a2324d6a.
The installed coordinator changed after the overnight attempt; its current
hash is not evidence of which bytes ran at 01:09. Preserve newer work.

Platform request: publish the new source/install receipt and reconcile the
launcher default with a real default-path process-contract test. Preserve
phase-specific content-free failure reason and provenance across final refusal.
Diagnose the retained prepare evidence before another approved cycle. Agree
whether early F2 is local archive timing only or requires the later LXC110
mirror; do not remove a recovery gate silently or manufacture an early mirror.
If mirror verification is deferred, bind it explicitly to the later F3/F4
admission rather than treating an F2 pass as complete backup qualification.

Adaptive: this receipt acknowledges the cycle failed before any retained scan
result; retain F2/F3/F4 and A1 blocked. No retrospective success receipt or
automatic repeat is authorized. Keep the independent host runner design,
original 04:15 restoration boundary and private-case custody unchanged.
