# F2 scheduled-execution reliability assessment — 2026-10-19

## Outcome

The October 19 F2 cycle did not fail an archive integrity check. The scheduled
Codex heartbeat arrived at 01:06:34 and TrueNAS task 1 had completed
successfully at 01:06:03, but the complete preflight was not retained before
the 01:20 invocation cutoff. No guard or archive scanner ran.

The current design is therefore not dependable enough to treat a scheduled
wake-up as an execution mechanism for a narrow safety window. The Codex task
remains useful as the supervising and evidence-reconciliation layer, but it
must not be responsible for assembling every slow or static prerequisite after
the window opens.

## Evidence classification

- **VERIFIED CURRENT STATE:** the daily heartbeat is active at 01:05
  America/Vancouver; the October 19 heartbeat arrived; task 1 succeeded; no
  scan ran; the later postcheck found no scanner, lease or F2 receipt.
- **UNKNOWN:** the exact cause of the observation gap between initial
  preflight and the later host observation. No retained evidence proves an app
  crash, host fault, model delay or tool failure.
- **ARCHITECTURAL INFERENCE:** a multi-step agent preflight with a 14-minute
  admission window has unnecessary scheduling and tool-latency sensitivity.
- **PROPOSAL:** move the slow, deterministic, read-only collection into one
  host-side preflight producer and leave final authorization and invocation to
  the supervising turn.

[OpenAI's scheduled-task guidance](https://developers.openai.com/training/walkthroughs/scheduled-tasks)
says local tasks depend on the computer being on and the desktop app running,
and that run history should be reviewed in the Scheduled view. It does not
provide a hard dispatch or completion-time guarantee suitable for this safety
boundary. The infrastructure guard must therefore remain authoritative for
timing and freshness.

## Proposed two-stage path

### Stage 1 — deterministic preparation

A disabled, source-reviewed host helper should gather only non-secret,
read-only facts that do not themselves authorize a scan:

1. installed guard/dependency hashes, ownership and modes;
2. fixed backup, TrueNAS and News schedules;
3. expected guest identities and running state;
4. exact current-cycle Proxmox backup job result and archive identities;
5. TrueNAS task-1 result when it becomes available;
6. lease-ready state and absence of an existing lock or receipt; and
7. a source commit, schema version, collection time and expiry.

The helper should write one bounded, root-owned, mode-0600 snapshot through an
atomic unique temporary file in a root-owned mode-0700 directory. It must not
run `zstd`, create an F3 receipt, acquire a lease, stop a service, enable a
timer or call a model. Missing or uncertain facts produce a content-free
NO-GO snapshot.

### Stage 2 — narrow supervised decision

The scheduled Stream A turn should perform one bounded call that:

1. verifies the snapshot schema, source pins, ownership, mode and freshness;
2. independently rechecks the volatile gates: current time, task completion,
   host load, competing processes, lease/lock/receipt absence and operator
   supervision;
3. refuses stale, partial, mismatched or prior-cycle evidence;
4. invokes the installed one-shot guard at most once only inside the approved
   start window; and
5. performs the existing no-child/no-lease/no-receipt postcheck.

The guard remains responsible for the outer deadline and archive bounds. A
Codex wake-up, a successful preparation snapshot or a scheduler `SUCCESS`
never substitutes for the guard result.

## Acceptance criteria

Before another F2 cycle can be called operationally dependable:

- target-Linux synthetic tests must prove stale-cycle, stale-time, wrong-pin,
  malformed, partial, symlink, ownership, mode and competing-work rejection;
- a disabled installation must prove exact hashes and no service/timer effect;
- a dry preflight must complete with measured margin before 01:20 without
  invoking the archive scanner;
- the next approved/active cycle must retain all three exit-zero archive rows
  and a clean postcheck; and
- the automation must pause on success, drift, safety failure or uncertain
  postcheck as already specified.

Until then, F2 remains **OPEN / UNMEASURED**. This correction does not advance
F3, authorize a full-stop drill, establish MacBook lab admission or run A1.

## First source candidate review

The platform owner produced a source-only candidate at `5958e365`. Its 12
focused tests pass when replayed independently, but it is not eligible for
target staging:

1. its slow collector reuses the full-drill `_schedule_ok` helper, which
   requires the 01:00, 02:00 and 03:00 TrueNAS tasks all to have completed;
   that condition is impossible during the intended 01:10–01:19 F2 window;
2. its test captures the snapshot at 03:10 and therefore does not exercise the
   actual F2 timing boundary;
3. its final guard rechecks only age and a supplied exclusion token, not the
   live lease/lock/receipt, competing-job, load and installed-pin gates; and
4. the source does not yet provide the required root-custody atomic snapshot
   writer/reader.

The owner received these exact counterexamples. The next candidate must have
an F2-specific task-1 completion rule while separately verifying the fixed
task 1/3/2 schedules, a real 01:07 fixture in which tasks 2/3 have not run, a
trusted clock and source-local dynamic recheck, and the custody tests listed
above. No installation follows from `5958e365`.

