# B60 execution-readiness gate

Use this gate after registration and again after booking. It is intentionally
stricter than confirming that the ledger accepted a record.

## Control plane

- Booking exists and names the intended registered owner and workload.
- State is `scheduled` before the window or `claimed` only by its expected
  runner after admission.
- Execution duration meets the workload minimum and the ledger maximum.
- The separately checked window includes the registry recovery reserve.
- `aster-lab-hours-dispatch.timer` is enabled and active; its next trigger and
  claim tolerance cover the booking start.
- Registry import and validation succeed.
- Installed release-manifest verification succeeds.
- Every registered runtime pin has valid root custody and hash.
- Runner kind is admitted by the reserved runner and routes to the intended
  transaction/adapter.
- A retryable session declares a bounded attempt deadline and a time-budgeted
  retry policy. An optional count ceiling may further restrict attempts, but
  the booking interval and restoration gate are the primary bounds.
- For a claimed V2 session, `attempt_state`, `attempt_count`,
  `retry_available`, attempt history, and current evidence directory agree.
- An independent read-only evaluator reviewed the final activated registration
  and exact booking without claiming it or initializing the backend. Its verdict
  and residual risks are recorded; deterministic blockers are resolved.

## Runtime path

- Source revision/tree, models, inputs and runtime are immutable and match the
  declared hashes.
- Required shared libraries load under the exact transient-service environment;
  do not rely on an interactive shell's loader path.
- Storage, host/LXC memory and device capacity have bounded headroom.
- The transient unit enforces any claimed network namespace, memory maximum,
  zero-swap or other resource policy. Verify the live cgroup/unit properties
  with an inert command.
- Output targets are empty or attempt-unique and cannot overwrite accepted
  artifacts.
- The adapter refuses unexpected arguments, identities, devices and outputs.

## Exclusivity and recovery

- Whole-host lease reports ready before admission.
- Shared operation and full-drain locks are absent before the run.
- No other booking remains claimed or unrestored.
- Accepted production GPU holder is exactly the registered baseline.
- Guardian is armed before drain; its deadline covers recovery.
- Cleanup proves transient unit, process, listener, device holder and temporary
  state absence.
- Postcheck proves the accepted model, binary, service, endpoint and affected
  timers are restored.

## Evidence and fault handling

- Kernel fault/reset/error capture starts before workload effects and uses
  case-insensitive matching appropriate to the driver.
- Resource measurements are bounded and cannot be forged by an unconditional
  result field. Prefer cgroup enforcement and source-local measurements.
- Receipt schema is closed, size-bounded and content-minimized.
- Result validation checks artifact hashes, counts, timing and identity.
- Any unverifiable control yields `NO_GO`; restoration still runs.

## V2 retry, release and promotion

- Retry is admitted only from `failed_restored` with `retry_available=true`.
- Any optional attempt-count ceiling permits the next attempt, and its complete
  deadline fits before booked end.
- Attempt evidence is unique and records the exact candidate pins used.
- A pin correction is installed and release-manifest validated before retry;
  material workload-purpose or runner changes use a new workload identity.
- Early release is refused while an attempt runs or restoration is incomplete.
- Release after effects preserves a recovery buffer and actual session outcome.
- Promotion is limited to bookings created with `--promotable`, preserves their
  duration and original times, and rechecks all protected windows.
- A monitor may report state and retry budget to the owning agent. Within an
  approved autonomous booking envelope, that agent may diagnose, repin,
  explicitly retry or release without another conversational approval.

## Verdicts

- **WILL RUN:** deterministic control path and inert prerequisites are proven;
  no first-use GPU/backend uncertainty remains.
- **LIKELY RUN:** control path is proven, but first booked GPU enumeration or
  model execution remains an acknowledged experimental uncertainty.
- **WILL NOT RUN:** a deterministic precondition, route, dependency, hash,
  duration or control check is known to fail.
