# Supervised full-inference drain — offline candidate

Status: architecture candidate; not installed, not enabled, and not approved
for live effects. This is a smaller alternative to the preserve-backend
cooperative controller. It is not the F2/F3 fault-injection or receipt drill.

## Finding

The established MacBook administration path is documented historically:
Jason's MacBook SSH identity reached `root@192.168.50.10` (Proxmox), with the
known host-key limitation recorded in the MacBook administration evidence.
The client-facing Aster path is separately `aster.elliottrook.com` → LXC104 →
internal LXC110, but that gateway is intentionally drained here. A direct
MacBook-to-model workload has not been demonstrated, so the first run proves
drain/recovery only. A usable experiment requires a separately named command
workload over the reviewed Proxmox administration path and is not implied by
this card.

## Bounded 30+15 pilot

The attended pilot is 30 minutes of lab time plus a 15-minute restoration
reserve. It requires a fresh source-bound backup/cycle and runtime preflight,
the host exclusion, owner heartbeat and monotonic cutoff. No reboot, PCI
rebind, VM 105 use, fault injection, benchmark batch or arbitrary model call
is included. The isolation pilot needs a fresh source-verified backup status
and accepted runtime checkpoint, but does not require the incomplete F2
retained-archive-integrity path or an F3 trusted receipt.

The current Proxmox→TrueNAS observer route is NO-GO after a bounded SSH
connect timeout; see `FULL-DRAIN-TRUENAS-OBSERVER-NO-GO-20261018.md`. That
route remains mandatory for any claim about the TrueNAS mirror, F2 archive
integrity, or F3 retained receipts, but it is not a gate for the narrower
attended no-file-mutation isolation pilot below.

### Narrow local-Proxmox pilot source mode

The first attended 30+15 pilot may use the separately named
`LocalProxmoxFullDrainSourceProducer`. It is authoritative only for this
narrow isolation run and must prove, from the current Proxmox host:

1. all three fresh positive-size 104/110/116 archive artifacts are from the
   current cycle;
2. the fixed enabled `backup-49999802-1365` all-guest `vzdump` job remains at
   `00:30`; and
3. exactly one current-cycle `vzdump` task is `OK`, has a valid Proxmox UPID,
   and its end time is after every required artifact and before the observation
   cutoff.

The producer must not call the TrueNAS observer in this mode. A separate
read-only Mac-mini observation may be recorded as nonauthoritative evidence,
but a failed or unavailable observer remains **NO-GO for mirror/F2/F3 claims**.
This mode does not mutate backup or model files and does not close F2 or F3.
Before any masks, the source producer must also report the existing manual
`local-ai-lease status` as `ready`. The pilot is attended: the supervisor must
not start the old manual controller during the window, and no unattended
recurring drain or automatic owner-death recovery is claimed.

The final release check must use `LocalProxmoxFullDrainValidator` (not the
TrueNAS-dependent `FullDrainValidator`). The pinned host entrypoint is
`/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/full-inference-drain/full_inference_lab_runtime.py` with
`PYTHONPATH=/usr/local/libexec/local-ai-lease/full-inference-drain`.
The supervised start command is:

    PYTHONPATH=/usr/local/libexec/local-ai-lease/full-inference-drain /usr/bin/python3 -B /usr/local/libexec/local-ai-lease/full-inference-drain/full_inference_lab_runtime.py --phase start --owner-id <owner> --admin-path-evidence <attestation> --cycle <YYYY_MM_DD> --session-start-epoch <epoch> --model-sha256 <sha256> --binary-sha256 <sha256> --unit-sha256 <sha256> --effect-authorized

The supervisor heartbeats with the same owner and exact lease identity using
`--phase heartbeat --lease-id <lease> --generation <generation>`, and restores
with `--phase restore` plus the same cycle and three hashes. If the owner
process dies, the supervisor uses `--phase resume` with the exact durable
identity, then the restore command. No watchdog or automatic recovery is
enabled by this card.

The `--owner-id` and `--admin-path-evidence` values are operator inputs, not
proof of MacBook custody. The actual SSH identity, pinned host key and
attended operator path must be independently checked before any live effect.
The phased CLI releases its process-level flock between commands, so this
packet does not claim continuous host exclusion or live readiness. A live run
remains NO-GO until a persistent supervisor holds the exclusion across the
full window, or the legacy controller is separately blocked by a reviewed
host change.

### Fixed drain inventory

1. Apply reversible runtime masks with `--now` to News ingest/digest timers,
   Aster Agent 104, Aster Speech 116 and accepted `aster-llama.service` 110.
2. Verify all five fixed entries are inactive and masked, and journal every
   intent/observation. Any ambiguity retains the lock and stops.

The accepted backend is not preserved during this candidate window. The
MacBook operator may only use an explicitly reviewed workload path after the
drain is proven; the existing direct `192.168.70.12:11435` endpoint is not
assumed reachable or admission-controlled.
The five-effect inventory is not proof that all B60 activity has stopped. Until
the GPU occupancy receipt and a deterministic device-admission boundary exist,
this card describes only known-consumer isolation; it must not claim host-wide
exclusive B60 access. Any unlisted render-node user during the window is a
hard stop and retains the lock for reconciliation.
If the persistent supervisor, fixed direct-backend wrapper, MacBook custody,
owner-loss recovery and occupancy gates are all independently ready, the first
attended 30+15 reservation should combine a three-request accepted-9B smoke
control with the drain/recovery proof. Without those gates, the combined run
is NO-GO and no isolation-only live outage should be scheduled merely to
produce a partial usability claim.

The named workload candidate for a later usable session is the B60 branch's
queued fresh accepted-9B control. It is a control candidate only: it must not
run until the operator path, fresh recovery checkpoint and post-drain
restoration are independently verified.
The persistent supervisor and workload boundary are designed separately in
`COOPERATIVE-FULL-INFERENCE-RECURRING-SUPERVISOR-DESIGN-20261018.md`.

### Recovery baseline

Before effects, capture fresh hashes and state for the accepted Qwen3.5-9B
Q4_K_M model, `llama-b11429` binary, `aster-llama.service` unit, GPU `xe`
binding, VM105 stopped/no B60 mapping, and LXC104/110/116 configuration.
Recovery must stop any lab process, restore the pinned accepted files/config,
start LXC110, run the exact production authentication probe and require its
success, then start LXC116 and LXC104, unmask/start the News timers, and run exact postchecks including
`scripts/check-aster-b60.sh`, service health, SYCL/GPU identity, schedule
state, and the source-bound client path. A failed or uncertain check retains
the lock for operator reconciliation.

## Explicit gates

- A fresh Proxmox host source adapter must prove the GPU and rollback VM state;
  historical documentation is not a live checkpoint.
- The MacBook SSH identity and host-key custody must be revalidated for the
  actual operator session; the historical pass does not authorize a new write.
- A named first workload and its exact admin command path must be reviewed
  separately. No direct backend client is accepted merely because `ss` shows a
  peer.
- The full drain candidate must pass disabled target-Linux staging and an
  independent review before any live service stop.
- Partial drain, owner-process loss, exact `resume_existing` identity and
  final local-Proxmox restoration validation must be demonstrated before a
  live run. If ownership is lost, the lock remains held until a supervisor
  resumes the exact lease or manually reconciles it.

This card is therefore feasible as a supervised drain/recovery prerequisite,
but it does not yet close the usable MacBook B60 experiment milestone. Any
later workload that mutates files, models or runtime configuration requires its
own stronger restore checkpoint and rollback card, including the TrueNAS/F2/F3
gates where applicable.
