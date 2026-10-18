# Recurring full-inference lab supervisor and first workload design

Status: offline design only. This document does not authorize staging, service
stops, model calls, a reboot, systemd enablement, or a remote push.

## Why the phased CLI is not enough

The current disabled entrypoint can start, heartbeat, resume and restore, but
its process-level flock is released between invocations. It is suitable for
the attended isolation proof only. It must not be presented as a recurring
lab-hours controller because a legacy controller could start between phases.

The smallest recurring design is one root-owned systemd service whose process
holds the shared host exclusion from acquisition until final restoration:

1. Read a root-owned, source-generated session manifest containing the cycle,
   lease ID/generation, accepted hashes, owner identity, hard lab end and News
   cutoff.
2. Run the local-Proxmox preflight and acquire durable full-drain state.
3. Keep the flock open, heartbeat at a fixed short interval, and enforce both
   the monotonic lab cutoff and the absolute News-safe deadline.
4. At cutoff, stop the named workload, run canonical restore, and run the
   `LocalProxmoxFullDrainValidator`.
5. Remove durable state only after every postcheck passes.

The unit is `Restart=on-failure` but has no automatic continuation authority:
after owner/process loss, a restarted instance enters recovery-only mode,
reacquires the exact lease identity, restores the fixed inventory and releases
the lock only after validation. It never resumes model work after owner loss.
If recovery cannot prove identity or state, it retains the lock for operator
reconciliation. The unit remains disabled until a separate live review proves
the old `local-ai-lease` controller is blocked or participates in the same
admission boundary.

The proposed unit needs root-owned state custody, `NoNewPrivileges`, a fixed
`ExecStart` pointing at the pinned entrypoint, a bounded `TimeoutStopSec`, and
no network or credential authority beyond the fixed probes and named workload
wrapper. It must not be a timer that starts a drain without a fresh
source-bound manifest.

## Independent watchdog and falsifiable plan

`Restart=on-failure` is insufficient for a hung owner. A separate
`full-inference-lab-watchdog.service` must run under an independent systemd
unit/timer and hold no workload authority. It reads only the durable session
state, supervisor PID/invocation identity, heartbeat age, monotonic deadline
and hard News cutoff. Its decisions are fixed:

- fresh heartbeat and before cutoff: observe only;
- stale heartbeat, missing owner, supervisor exit or process identity drift:
  mark the lease recovery-only, send the fixed TERM then KILL sequence to the
  recorded supervisor PID, and wait for the exclusion to be released;
- after exclusion acquisition: run only exact restore commands and the
  `LocalProxmoxFullDrainValidator`; and
- any uncertainty, failed postcheck or missed cutoff: retain the lock and
  durable journal for operator reconciliation.

The watchdog must never restart the lab workload, extend the deadline, accept
new owner strings, or clear the lock from a failed recovery. The fixed hard
wall cutoff is enforced by both the supervisor's monotonic clock and the
watchdog's independently computed deadline; the earlier News-safe deadline
wins. Restoration must include LXC110 authenticated warm-up before Speech,
Agent and News timers, followed by exact accepted model/binary/unit/GPU/auth,
service and timer checks.

The installed manual helper is confirmed to share the `/var/lib/local-ai-lab`
directory flock during its acquisition call, but it does not inspect the
candidate's separate full-drain marker. That prevents simultaneous acquisition
only while both callers hold the flock; it does not cover the phased CLI gap.
Before recurring mode can be live, the persistent supervisor must hold the
same exclusion across the full window and the legacy helper must either refuse
when the durable full-drain marker exists or be separately blocked by a
reviewed host change. A status probe alone is not exclusion. The supervisor
and watchdog must also verify the marker and exact lease identity before any
effect.

The offline acceptance plan is falsifiable and has no host effects:

1. Fake fixed transport: prove start writes the durable marker/state before
   the first mask, holds the exclusion, and rejects a simulated legacy
   acquisition.
2. Nonzero effect: return failure for each mask, warm-up, start and restore;
   prove no failed command is journaled as observed and the lock remains.
3. Hung owner: freeze heartbeat after the first mask; prove the independent
   watchdog marks recovery-only, kills the exact recorded process, restores
   all five consumers in order, validates LXC110 warm-up and retains the lock
   on any failed postcheck.
4. Hard cutoff: advance wall and monotonic clocks independently; prove the
   workload is stopped at the earlier lab/News deadline and no extension is
   accepted.
5. News boundary: make the next ingest fall inside the reserve; prove
   acquisition is refused and make a timer restoration failure retain state.
6. Identity drift: alter PID, invocation, owner, lease, generation or marker;
   prove recovery refuses to act and does not clear state.
7. MacBook disappearance: remove the client heartbeat/connection while the
   supervisor remains healthy; prove the watchdog does not infer identity from
   connection presence and follows only the owner heartbeat/deadline contract.
8. Final baseline: return active/enabled service state but drift the model,
   binary, unit, GPU, auth or schedule; prove `LocalProxmoxFullDrainValidator`
   refuses release.

The resulting evidence must include the fake transport transcript, state and
journal hashes, expected command sequence, failure injection, watchdog kill
receipt and final lock state. A passing synthetic suite does not authorize
host installation or live recurring lab hours.

## GPU occupancy boundary

Stopping the five known consumers is not equivalent to proving that all other
B60 activity has stopped. Before any claim of exclusivity, the host adapter
must inventory the actual render node and its launch paths with bounded,
read-only observations equivalent to:

```sh
stat -Lc '%t:%T %a %U:%G %n' /dev/dri/renderD128
fuser -v /dev/dri/renderD128
ps -eo pid=,ppid=,user=,etimes=,cmd= --forest
systemctl list-units --type=service --state=running --no-legend --no-pager
systemctl list-timers --all --no-legend --no-pager
```

The sanitized occupancy receipt must bind each render-node user to PID,
start-time, cgroup/unit, executable identity and observation time, without
exporting command secrets. Capture it immediately before masks, during the
workload at a fixed interval, after workload stop, and after restoration. The
before/during/after sets must distinguish the accepted baseline service,
approved workload process and every other user; `systemctl active` alone is
not evidence.

The current design has no deterministic host-wide admission boundary that
prevents an unlisted privileged process from opening `/dev/dri/renderD128`.
Therefore the first run is explicitly **known-consumer isolation**, not
“exclusive access to the B60.” A new render-node PID, cgroup or executable
outside the approved set is a hard stop: stop the workload, restore the fixed
inventory, retain the lock if any observation is uncertain, and report the
run as failed. A future true-exclusivity release needs a separately reviewed
host device-admission boundary; it cannot be inferred from the five masks.

The offline false-new-consumer test inserts an unlisted render-node user into
the during snapshot and independently changes its PID/cgroup identity. The
candidate must reject both cases, emit no workload admission, preserve the
failure journal and require recovery. A passing test proves only detection
logic, not host-wide prevention.

## First named workload for the full-drain path

The first usable full-drain workload is **accepted-9B direct-backend control
v1**, a separate control profile, not the Aster full-path benchmark. It is
invoked by the MacBook through the reviewed MacBook→Proxmox administrative
path and executed by a pinned host wrapper using `pct exec 110`; the API key
never leaves LXC110. The wrapper accepts no arbitrary command, URL, model or
file path.

Its fixed contract is:

- model `aster-qwen3.5-9b` / Qwen3.5-9B Q4_K_M;
- accepted `llama.cpp b11429 SYCL/Level Zero` binary and unit hashes from the
  same fresh preflight;
- temperature `0`, reasoning off, maximum `256` output tokens;
- the frozen 20-case request set from
  `a1-full-path-9b-candidate-profile-v1.json`, with tools disabled and one
  attempt per case;
- a 20-minute maximum batch wall time and one-minute per-request timeout;
- owner-only raw answers and credentials; shared evidence contains only
  content-free request IDs, timing, exit status and profile digests; and
- no retries after an uncertain request, no filesystem/model mutation and no
  administrative tool calls.

This is deliberately labelled a direct-backend control. It does not qualify
the Aster gateway, Companion display, or sysadmin capability. The existing
full-path candidate remains a separate application-mode benchmark: it needs
LXC104's isolated gateway/sidecar and an application-only lease that keeps
LXC110 active, so it cannot run inside this full-drain session.

## Admission and release gates

Before a future workload run, a new card must bind the wrapper digest, the
MacBook SSH identity and pinned host key, the source-generated manifest, the
lease identity/generation, and the exact case/profile digests. The first
workload run must be manually attended and must finish before the hard News
cutoff with the full restoration reserve intact. A successful isolation pilot
does not satisfy these gates and does not authorize this workload.

The first workload remains blocked until the persistent supervisor, wrapper,
MacBook custody proof, and a dry-run of owner-loss recovery are independently
reviewed. No Aster/Qwen sysadmin authority is inferred from this control.

The offline implementation candidates are
`scripts/local-ai/full_inference_lab_supervisor.py` and
`scripts/local-ai/full_inference_lab_workload.py`, with synthetic tests in the
corresponding `test_` files. They are not part of the 14-file disabled-stage
packet and are not installed, enabled or callable on the target host.

## Recommendation: combine the first useful pilot, conditionally

Do not spend a live outage on an isolation-only run if the workload gates are
ready. After disabled target-Linux proof, persistent supervisor/legacy
exclusion, MacBook identity and pinned host-key proof, fixed wrapper review,
owner-loss dry-run, and GPU occupancy checks all pass, combine one tiny control
with the first attended drain/recovery pilot:

| Elapsed | Bounded action |
|---|---|
| 00–05 min | Recheck source-bound backup, runtime, lease, News cutoff and GPU occupancy; acquire the persistent supervisor lock. |
| 05–10 min | Apply and verify the five masks; reject any unlisted render-node user. |
| 10–15 min | Confirm settled known-consumer isolation and authenticated LXC110 warm-up. |
| 15–20 min | Run exactly three no-tool accepted-9B direct-backend control requests from the frozen set through the fixed MacBook→Proxmox wrapper; no retries. |
| 20–30 min | Capture content-free control/occupancy evidence and stop the workload; leave unused time as safety margin. |
| 30–45 min | Restore with the LXC110 warm-up gate, exact validator and before/during/after occupancy comparison. |

This saves a second outage while keeping the first workload deliberately
small. The three-request smoke profile is not the 20-case A1 benchmark and
cannot establish quality, full-path behavior or sysadmin capability. If any
one of the prerequisites is missing, the combined run is **NO-GO** and the
candidate remains offline; do not weaken source, rollback, owner, occupancy or
MacBook-custody checks to make the schedule fit.
