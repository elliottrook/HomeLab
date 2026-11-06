# Actual 35B reasoning-on model trial — November 6

The production adapter is operational and a real local B60 model trial ran in
booked lab hours. Result: **FAILED_RESTORED**, not a promotion or programme pass.
The fixed Qwen3.6-35B-A3B Q4_K_M loaded on the accepted FP16 SYCL runtime with
reasoning mode on and all41layers offloaded. The two-request compatibility
workload exited nonzero. Production entry restoration and shared release
completed automatically at **11:46:06 Vancouver**, before the12:21 deadline,
without assisted recovery. No model/device failure was retried.

## Measured result and its limits

Readiness snapshot, before the fixed requests:

| Observation | Actual result |
|---|---:|
| GPU-resident memory | 20,065,232KiB =19.14GiB |
| GTT resident | 65,512KiB |
| Process RSS | 736,200KiB =0.70GiB |
| Candidate cgroup peak at readiness | 1,249,427,456bytes =1.16GiB |
| Enforced candidate cgroup limits | 14GiB, swap0, CPU400%, Tasks256 |
| Affirmative GPU layer offload | 41/41, SYCL |
| Kernel reset/device/OOM hazard count through release | 0 |

These are local measurements, not vendor or other-GPU claims. Cgroup charge
and process RSS are not total host page-cache/driver memory; the readiness
snapshot is not a continuous peak/thermal/soak measurement. Model/hash,
source closure and resource floors were independently checked before use.

The server journal retained numeric timing for two generations:

| Request | Prefill | Decode | Generated tokens |
|---|---:|---:|---:|
| 1 | 464.06ms /32tokens | 11,511.8ms | 514 |
| 2 | 458.93ms /47tokens | 20,093.1ms | 1024 |

The second generation reached the declared1024-token ceiling. The fixed guest
request program rejected the workload and returned nonzero; the host then
restored rather than accepting a truncated/invalid answer. Token-limit
rejection is the leading diagnosis, **not a retained explicit finish_reason**.
The collector discarded its partial per-request metadata on failure and the
host retained only the fixed SessionError class. HTTP status, precise rejected
finish reason and first-answer semantic correctness therefore remain unknown.
No answer or hidden reasoning was exported or retained. The numeric generation
timings do not establish complete useful-answer latency, full-Aster p50/p95,
grounded capability improvement or semantic acceptance.

The resource-fit gate for this exact artifact/runtime has positive evidence.
The compatibility/usable-answer gate failed. The27B+ reasoning-on capability
and matched fresh9B median/p95 deliverable remains unaccepted.

## Actual execution and restoration

R1's11:12 attempt stopped before claim/model/drain on a real latest-job cache
ordering failure. It is retained as pre-claim NO-GO and was not replayed.
The distinct R2 booking b60-exclusive-20261106-day-r2 was11:36–12:21, reserve12:36.
Its six-source adapter verified an authenticated historical ordered TrueNAS
chain and separately required unchanged current task metadata, exact current
mirror/archive identities, real retained zstd age and whole Proxmox backup
completion. No backup jobs/schedules, observer permissions or credentials
changed. The actual scan remained10:28:40, not a renewed timestamp.

R2 claimed at11:39:10 after fresh admission/checkpointing and independent
guardian arming. The candidate used only its distinct private service mount
namespace; no guest reboot or persistent pct mount was made. On workload
failure the exact candidate cgroup was fenced, its namespace disappeared,
the temporary production-namespace directory was removed, staging root/file
custody returned to700/400 root ownership, and the base controller restored
all captured entry configurations and previously active scheduled work.
The ledger/source terminal is FAILED_RESTORED at epoch1793990766(11:46:06).
Owner/guardian tasks and shared lease/drain/operation markers were absent
following actual release. No manual restore, reset, reboot or GPU retry occurred.

Independent read-only reconciliation reverified all five guest checkpoints
(104,110,114,115,116), exact candidate absence and staging custody. Core Aster,
accepted llama and Speech services were active. A later direct unit snapshot
at epoch1793992079 found no state/enablement mismatches. Timers had their
restored entry activation states and future triggers. No observer restarted,
stopped or replayed scheduled work to force a snapshot match.

Strict postcheck failures are preserved, not converted into green receipts.
An observer indexing bug assumed the pinned _gpu_users frozenset was a list;
that read-only bug was corrected with no production effect. Another observation
returned a unit-state mismatch without retaining the individual row; a later
complete direct unit snapshot matched with no intervening B60 mutation. The
exact transient cause is unestablished; timer activity is not asserted as proof.

## Separate configuration change after release

The strict current-entry comparison also detected a new persistent mp0:
local-lvm:vm-110-news-video-xpu at /opt/aster-news-video-xpu. The configuration
mtime is11:48:06, after B60's11:46:06 release. Repeated observations showed
that excluding this one added line **in memory only** reproduces the exact
captured entry mount hash; all other filtered configuration fields match.
This trial made no pct mount changes. B60 did not remove, modify or restore
over the separately added News volume, and did not access its data.

The separate reconciliation explicitly records current_full_entry_accepted=false.
It proves B60's cleanup/restoration facts and names the subsequent delta;
it does not certify the new News configuration or invent its authorization.
The queried owning News branches contained design records but no receipt for
this live volume change. No peer is declared unresponsive and publication is
not proof of reading. Before another full-stack trial, reconcile that owner's
exact change receipt and any new GPU consumers/schedulers with shared admission.

Owned coordination question: please publish exact commit/path/hash receipt for
the11:48 News-XPU volume addition and its consumer/scheduler/lease boundary.
B60 preserved it. No new conversational model-change approval is being requested.

## Evidence and next concrete action

Sanitized immutable outcome and all root record hashes are in
[evidence/20261106-model-trial/r2-outcome.json](evidence/20261106-model-trial/r2-outcome.json).
Key root receipts:

| Root record | SHA256 |
|---|---|
| exclusive-sessions/b60-exclusive-20261106-day-r2/model-terminal.json | 425ce9d83a8ecb4aa91f025196def2d4ce5066c791ea8d9bb5f936d85da0a3fe |
| exclusive-releases/b60-exclusive-20261106-day-r2.json | 3322ced1b9a805cb825c7c9050281115f4a80451293f247c5e4d3138613e8a7c |
| exclusive-sessions/b60-exclusive-20261106-day-r2/model-residency.json | b494824399807e946d3dfb738e095870fe61152b50b0a1dfc38c3d1730347e04 |
| arming-receipts/b60-exclusive-20261106-day-r2-model.json | 90d309526c3ec84a171025acfddf2311da1536e7eaf7d5f0bfde183297576d8f |

151 offline B60 tests passed before this real trial; fake tests are not its
qualification. Runtime/model recovery anchors remain the accepted b11429 binary
0404f751…0de6c5, unit a4c75169…fd4cb3 and9B model cd76ec20…f2a13. No model
promotion, global driver/package/boot, GPIO/household effect, private evaluation,
credential export, TTS or GPT-routing change occurred.

Next: retain complete bounded per-attempt status/finish reason/timing/token
metadata even on request failure, preserving zero retries and no reasoning
text. Reconcile the later News consumer/schedule inventory. Freeze the fresh
accepted9B complete-useful-answer baseline and harder held-out task contract
before tuning thinking effort or running finalists. Keep source-bound booked
admission and independent restoration for every actual model change. Programme
automations remain active; no final acceptance, pause or sleeping-background
execution is claimed. No new conversational approval is missing within scope.
