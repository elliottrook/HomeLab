# Combined supervised accepted-9B pilot — live run card

Status: prepared but not approved for live effects. The new combined source
must first pass its separate disabled-install approval and target-Linux review;
the earlier phased 14-file approval does not apply. This is not the F2/F3
fault-injection or receipt drill.

## Finding

The established MacBook administration path is documented historically:
Jason's MacBook SSH identity reached `root@192.168.50.10` (Proxmox), with the
known host-key limitation recorded in the MacBook administration evidence.
The client-facing Aster path is `aster.elliottrook.com` → LXC104 → internal
LXC110, and that path is intentionally unavailable during this pilot. The
fixed workload is a bounded, three-request loopback control in LXC110; it is
not an arbitrary MacBook model client and does not claim host-wide GPU
exclusivity.

## Bounded 30+15 pilot

The attended pilot is exactly 30 minutes of lab time plus a 15-minute
restoration reserve. The supervisor holds the host exclusion, sends owner
heartbeats, runs the fixed three-request smoke, and enforces a monotonic
cutoff. No reboot, PCI rebind, VM105 use, fault injection, benchmark batch,
or arbitrary model call is included. The pilot needs a fresh source-verified
backup status and accepted runtime checkpoint, but does not close F2 or F3.
The operator remains present on the verified MacBook administration session for
the complete 45-minute reservation and watches the receipt, cutoff, and
restoration evidence; disconnection or uncertainty is a stop condition.

During the 30-minute window this is an explicit product outage: Aster
Companion requests, LXC104 Aster Agent, LXC116 Speech, LXC110 production
Qwen3.5 service, and News ingest/digest are unavailable. Backup schedules,
TrueNAS services, and unrelated non-GPU services are not part of the drain.
The 15-minute reserve is for restoration and evidence, not additional lab
work. If restoration is not complete by the deadline, the lock is retained
and the operator reconciles the outage manually.

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

The final release check uses `LocalProxmoxFullDrainValidator` (not the
TrueNAS-dependent `FullDrainValidator`). The exact source tip and hashes are
in `COOPERATIVE-FULL-INFERENCE-PILOT-DISABLED-INSTALL-CARD-20261018.md`.
The target artifact checkpoint must record SHA-256 values for:

| Artifact | Target path |
|---|---|
| Qwen3.5-9B Q4_K_M model | `/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf` |
| SYCL `llama-server` | `/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server` |
| production systemd unit | `/etc/systemd/system/aster-llama.service` |

The target preflight must also verify, read-only, the existence and expected
identity of `/usr/bin/systemd-run`, `/usr/sbin/runuser`,
`/usr/local/sbin/aster-llama-production-auth-probe`, and the staged
`/usr/local/sbin/aster-llama-lab-smoke`; no replacement or installation is
permitted during the pilot.

The pinned host entrypoint is
`/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/full-inference-pilot/full_inference_lab_runtime.py` with
`PYTHONPATH=/usr/local/libexec/local-ai-lease/full-inference-pilot`.
The single supervised command is:

    PYTHONPATH=/usr/local/libexec/local-ai-lease/full-inference-pilot /usr/bin/python3 -B /usr/local/libexec/local-ai-lease/full-inference-pilot/full_inference_lab_runtime.py --phase pilot --owner-id <owner> --admin-path-evidence <attestation> --cycle <YYYY_MM_DD> --session-start-epoch <epoch> --model-sha256 <sha256> --binary-sha256 <sha256> --unit-sha256 <sha256> --effect-authorized

This is one bounded process: it performs source preflight, captures the
accepted production GPU identity, drains the fixed five consumers, runs the
three-request control on loopback port 11436, heartbeats through the deadline,
proves lab scope/listener/process/GPU absence, and restores through the final
validator. If the owner process dies or restoration becomes uncertain, the
lock remains for supervised reconciliation; no unattended watchdog is enabled.

The `--owner-id` and `--admin-path-evidence` values are operator inputs, not
proof of MacBook custody. The actual SSH identity, pinned host key and
attended operator path must be independently checked before any live effect.
The operator must capture, from the unlocked MacBook and without exposing
private key material, the identity fingerprint (`ssh-add -l -E sha256`), the
pinned `known_hosts` entry, and a successful read-only proof using
`ssh -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes
-o UserKnownHostsFile=<pinned-known-hosts> root@192.168.50.10 'hostname; id -u'`.
The evidence must show the expected Proxmox host and UID 0 before the pilot is
allowed to start. A failed, interactive, or differently keyed connection is
NO-GO.

### Fixed drain inventory

1. Apply reversible runtime masks with `--now` to News ingest/digest timers,
   Aster Agent 104, Aster Speech 116 and accepted `aster-llama.service` 110.
2. Verify all five fixed entries are inactive and masked, and journal every
   intent/observation. Any ambiguity retains the lock and stops.

The accepted production backend is not available during this window. The
MacBook operator must not use the direct `192.168.70.12:11435` endpoint or
send arbitrary requests; only the fixed in-guest three-request control is
allowed after the drain is proven.
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
Recovery must stop any lab process and independently prove the lab scope,
listener, process, and GPU handle are absent; restore the pinned accepted
files/config; start LXC110; run the exact production authentication probe and
require its success; then start LXC116 and LXC104 and unmask/start the News
timers. The evidence bundle must include the source and target artifact
hashes, drain/restore journal, pre/post service and timer state, successful
auth probe, `scripts/check-aster-b60.sh`, SYCL/GPU identity, schedule state,
the content-free smoke receipt, and the restored source-bound client path.
A failed or uncertain check retains the lock and the product outage remains
in operator-reconciliation state.

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
