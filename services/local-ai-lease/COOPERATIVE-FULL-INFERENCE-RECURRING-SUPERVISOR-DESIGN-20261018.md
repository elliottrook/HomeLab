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
