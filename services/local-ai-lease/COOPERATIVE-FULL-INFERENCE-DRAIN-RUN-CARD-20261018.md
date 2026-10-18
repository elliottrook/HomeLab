# Combined supervised accepted-9B pilot — live run card

Status: disabled stage installed and verified; live effects are not approved.
The installed source is `b43d4971`, bound to the exact 20-file manifest in
`COOPERATIVE-FULL-INFERENCE-PILOT-DISABLED-INSTALL-CARD-20261018.md`. The
earlier phased 14-file approval does not apply. This is not the F2/F3
fault-injection or receipt drill.

## Installed disabled-stage evidence

The approved source-only stage is present at
`/usr/local/libexec/local-ai-lease/full-inference-pilot/` on Proxmox as 19
`root:root` mode-0644 files in a root-only directory. The fixed LXC110 wrapper
is present at `/usr/local/sbin/aster-llama-lab-smoke` as `root:root` mode 0750.
All 20 installed SHA-256 values match the frozen manifest. Target-Linux
preflight returned 10 modules, 5 drain effects, 11 restore effects and
`effects=not-attempted`; 47 focused target tests and wrapper syntax passed.
The postcheck found the manual lease `ready`, all five production consumers
active, and no listener on port 11436. No model call, unit/timer install,
service stop, or remote push occurred.

This evidence authorizes no live effect. Before the pilot, repeat the
read-only baseline and MacBook custody checks below; if any installed hash,
service state, listener state, or path differs, the pilot is NO-GO.

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
The selected operator remains present on the verified administration session for
the complete 45-minute reservation and watches the receipt, cutoff, and
restoration evidence; disconnection or uncertainty is a stop condition. The
standard mode requires the verified MacBook custody described below. A separate
Mac-mini Stream A control-only mode may supervise this fixed in-guest smoke if
explicitly approved, but it does not prove MacBook custody, client handoff, or
direct MacBook model access.

The concrete reservation is defined at the final gate as `S` (the recorded
start epoch): lab work is `[S, S+1800)`, restoration is `[S+1800, S+2700)`,
and the next News ingest epoch `N` must satisfy `S+2700+300 <= N`. Immediately
after MacBook custody is proven, the operator must run the read-only command
`pct exec 114 -- systemctl list-timers --all --no-legend --no-pager
news-aggregator-ingest.timer`, record its next-run epoch as `N`, and either
select the first start time satisfying that
inequality or declare the pilot NO-GO. A stale or missing `N` is not a valid
window.

The latest read-only schedule observation recorded next ingest at 23:02:15 UTC
(16:02:15 Vancouver), followed by approximately 17:02 Vancouver, with the
digest at approximately 17:15. This makes 16:05–16:50 Vancouver a conditional
candidate slot only if the final custody, hash, and timer checks occur before
16:05 and confirm the later ingest as `N`: with `S=16:05`, restoration ends at
16:50, the five-minute margin ends at 16:55, and `16:55 <= N≈17:02`. Otherwise
the operator must recompute `S` and `N` rather than reuse this slot.

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

The first live workload is the fixed accepted-9B three-request control already
specified by the installed wrapper. There is no later or separate workload in
this card, and no B60 branch workload or arbitrary client request is included.
The persistent supervisor and workload boundary remain documented separately in
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

The pilot may start only when all of these are true:

1. The installed 20-file manifest and wrapper hashes match the disabled-stage
   card; target paths, modes, and required executables are unchanged.
2. The current Proxmox backup source check passes, the manual lease is
   `ready`, the accepted model/binary/unit hashes match, VM105 is stopped and
   unmapped, and the GPU `xe` baseline is current.
3. In standard mode, the MacBook fingerprint, pinned host key, read-only UID-0
   proof, and attended operator path are captured for this session. In the
   separately approved Mac-mini control-only mode, the Mac-mini session and
   operator identity are captured instead, with an explicit record that no
   MacBook custody or client handoff is claimed.
4. The post-custody News timer check records a future `N` satisfying the exact
   30+15+5-minute window inequality above.
5. The fixed production GPU holder is the exact LXC110
   `aster-llama.service` cgroup identity; after masking, no GPU holder remains.
6. The operator explicitly accepts the Aster/News outage and remains present
   for the whole reservation.

The run stops and retains the lock on any nonzero or uncertain drain command,
new/unlisted GPU holder, listener/process/GPU-handle residue, stale heartbeat,
monotonic or wall-clock cutoff, failed smoke receipt, failed authentication
probe, failed restoration postcheck, changed hash, or lost operator session.
The lock is not cleared to make the outage appear healthy; reconciliation is
required. A successful run must produce every restoration artifact listed
above. This card does not close TrueNAS mirror, F2/F3, or host-wide GPU
exclusivity gates.
