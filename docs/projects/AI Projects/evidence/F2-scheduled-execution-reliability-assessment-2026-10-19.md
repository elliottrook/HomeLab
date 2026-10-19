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

The corrected source-only candidate at `b39c4be2` fixes the task-1 timing rule
and adds dynamic probes and snapshot-custody code, but independent review
found another target blocker. Its common custody helper requires `st_nlink ==
1` for both files and directories. A normal private Unix directory has a link
count of at least two; a disposable mode-0700 directory measured `nlink=2`.
The positive custody tests are skipped when the suite is not root, so the
reported Mac suite did not exercise this path. The snapshot reader also
performs an `lstat` followed by a path-based read, leaving a replacement race,
and the final guard does not yet enforce the trusted local cycle/start window,
live lease status, host load or the complete installed dependency pin set.

The owner received these additional counterexamples. The next source review
requires descriptor-based no-follow reading and `fstat`, a bounded payload,
directory `fsync` after replacement, target-root custody tests, and all final
dynamic gates. `b39c4be2` remains uninstalled.

The next source-only revision at `59e50fa9` corrects the directory-link rule,
uses a bounded no-follow descriptor read, syncs the parent after replacement,
and adds trusted date/window, lease, load, process and installed-pin probes.
Its focused Stream A replay passed 21 tests with three root-custody positives
skipped on macOS. The F2 core may proceed to a release wrapper and target-
Linux review only if that wrapper owns the clock, exclusion token and complete
fixed pin map; none may be caller selected. No F2 file is installed from this
commit, and F2 remains open until the target-root tests and measured cycle
pass.

The release-engineering revision at platform commit `5e77cd7b` removes the
synthetic token and uses the existing `/var/lib/local-ai-lab` directory flock.
Its separate disabled-install card pins two new modules, six existing
dependencies, exact ownership/modes, absent-state rollback and target-root
tests. Stream A independently verified that the two target files and child
snapshot directory are absent, the existing state root is root-owned mode
0700, all six live dependency hashes match, and both source hashes match the
card. This makes the **F2 disabled installation review-ready**; it is not yet
installed and is not authorization to capture a snapshot or run a scan.

Jason approved that bounded disabled installation. The fresh host preflight
matched the card, and the four source/test files were copied only to a private
temporary staging directory. The pre-install target-Linux suite then stopped
the operation at 7/8 passes: the missing-snapshot test expected an error
containing `custody`, while the reader correctly returned `snapshot is
unreadable`. The root-owned positive snapshot round trip passed. No production
module or state directory was installed, and no service, timer, lease, scan,
receipt, GPU or model effect occurred. The platform owner received the exact
failure; the approved installation may resume only after the corrected test
passes against the unchanged pinned source or a newly reviewed source card.

The platform owner corrected only the failing test expectation in commit
`56c43bdc`; both reviewed module hashes remained unchanged. The corrected
target-Linux suite passed 9/9, including root custody, and the approved
installation then completed. The two installed modules match the release
card, their private state directory is root-owned mode 0700 and empty, and a
clean postcheck found no snapshot, receipt, lease, scan or service/schedule
regression. Temporary staging was removed and the absent-state rollback marker
was retained. See the
[disabled-install result](F2-deterministic-preflight-disabled-install-2026-10-19.md).
This closes only deterministic-preparation installation; F2 remains open
until a fresh cycle produces all three bounded archive rows.

## Remaining scheduler integration gap

After installation, Stream A re-read the active Codex automation. It still
wakes at 01:05 and instructs the agent to perform the original multi-step
preflight and invoke the diagnostic guard directly. It does not call the new
snapshot/fixed-wrapper entry points. Consequently, the successful disabled
installation alone does not prevent another missed start window.

This is a design mismatch, not an archive or production failure. Official
OpenAI scheduled-task guidance describes scheduled work as an app-managed
task whose local execution depends on the computer and desktop app remaining
available; it does not establish a hard dispatch deadline. The corrective
design is therefore a platform-owned, hash-pinned one-shot preparation and
final-gate schedule, with Codex reduced to read-only supervision,
reconciliation and reporting. The platform owner has been asked to prepare
that package offline. No unit or timer is installed or enabled by this
assessment, and the existing heartbeat must not be represented as sufficient
for the next F2 cycle until the invocation paths are reconciled.

## First deterministic schedule candidate review

The platform owner produced the requested disabled, source-only candidate at
commit `7baa171d`. Its intended structure is correct: a non-persistent 01:07
preparation timer, a non-persistent 01:10 final timer, no retry, hardened
one-shot services and a content-free terminal state. The reported repository
suite passed 331 tests with eight expected skips. Independent source review
found six blockers before target staging:

1. the installed snapshot guard permits 90 seconds of freshness, but a
   snapshot captured at 01:07 is at least about 180 seconds old at the first
   permitted 01:10 final invocation;
2. the proposed writable scheduled-state directory is absent on the host and
   neither the units nor the release card creates it before applying
   `ProtectSystem=full`;
3. the observer's validated three archive rows are discarded, leaving only a
   `complete` marker that cannot satisfy F2's retained-evidence condition;
4. the coordinator's outer `subprocess.run` timeout can kill the observer
   parent without proving termination of the observer's separate archive
   process group;
5. scheduled-state reads and writes lack the no-follow, bounded, atomic and
   custody checks already required for the snapshot; and
6. focused tests do not exercise the real timer gap, retained result,
   process-group timeout, state custody or installed systemd runtime.

These are fail-before-effect findings. No file from `7baa171d` was staged,
installed or enabled. The owner received the exact counterexamples and was
asked for a revised source/card. The disabled preparation modules already on
the host remain unchanged and production remains available.

The subsequent revisions closed those review findings in stages. Commit
`4342f7e7` moved preparation to 01:09, added the fixed state directory,
retained the bounded observer projection and added process-group timeout
handling. A disabled installation of that revision was then superseded before
activation. Commit `c99a241f` added no-follow state-directory custody, exact
archive row validation and explicit systemd control-group cleanup. Final
commit `56fcf4f3` added the missing 8 KiB output bound and complete state-file
writes. The platform install receipt is recorded at `01923cfb`.

Stream A independently verified the final installed hashes against the card,
root ownership/modes, the root-owned rollback checkpoint, an empty scheduled
state directory, absent preflight snapshot, successful installed import and
calendar resolution for 01:09/01:10 Vancouver. Both timers and both services
remain disabled and inactive. The lease is `ready`; Aster Agent, accepted
Llama, Speech and both News timers remain active. No daemon reload, timer
enablement, start, capture, scan, lease, service stop or model call occurred.

This closes the disabled scheduler installation only. Activation remains a
separate production change. F2 remains open until one activated fresh cycle
retains a complete validated three-row result and clean postcheck.

