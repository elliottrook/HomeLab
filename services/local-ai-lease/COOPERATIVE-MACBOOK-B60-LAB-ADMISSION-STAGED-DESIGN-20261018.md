# MacBook-usable B60 lab admission — staged offline design

Status: offline implementation and review only. No target installation,
service drain, schedule, model admission, or exclusivity claim is authorized
by this document.

## Outcome and honest boundary

The goal is a usable MacBook Codex lab session on the shared GPU host while
keeping daytime Aster services recoverable. The smallest safe path is a
source-bound, persistent lease held by one supervisor, with a fixed workload
wrapper and independently tested recovery.

The first release can prove only **known-consumer isolation**: the four named
daytime consumers are stopped, the approved lab workload is admitted, GPU
occupancy is observed, and the consumers are restored. It cannot prove that a
different privileged process will not open `/dev/dri/renderD128` between
observations. Host-wide exclusivity requires a separate device-admission
boundary (for example a reviewed cgroup/device policy or an equivalent
mediated GPU service). It must not be inferred from systemd masks or a clean
occupancy snapshot.

## Implemented offline contract

`scripts/local-ai/lab_workload_admission.py` now defines a disabled candidate
that admits a request only when all of these match the durable lease manifest:

- the MacBook owner identity and pinned `SHA256:` client-key fingerprint;
- the pinned Proxmox host-key SHA-256;
- lease ID and generation;
- the source/runtime digest and fixed workload-profile digest; and
- the verifier-owned current time inside an issued/expiry window capped at the
  approved 45-minute session.

Replay IDs are stored in a lease-owned, file-locked durable store, so a
verifier restart cannot reopen an admitted request. The returned receipt is
content-free and contains no key, prompt, answer, credential, or raw
caller-supplied ID. The verifier does not open a socket or grant GPU access.
Synthetic tests cover a matching request, identity/key drift, source/profile
drift, malformed or overlong manifests, verifier-clock expiry, restart replay,
and unsafe request IDs.

## Staged gates

### A — Offline contract and controller

Evidence: cooperative session tests, admission tests, supervisor/workload
tests, and the fixed source/run cards. The controller must hold the shared
exclusion from acquisition through restore, persist owner/lease/generation,
heartbeat while working, and enter recovery-only mode after owner loss.

Gate: all synthetic tests pass; no candidate is installed or enabled.

### B — Target-Linux disabled install

Install only the pinned admission module, its tests, the source-bound
producer/adapter, and the reviewed supervisor/workload files into a private
inactive directory. Verify imports, hashes, ownership/mode, and target tests.
Prove no unit, timer, listener, lease state, model request, or service change.
The replay store must be under a private root-owned lease directory with a
pinned per-lease-generation filename; the installed adapter must reject
symlink/hardlink replacement, missing state after lease start, and any parent
ownership or mode drift. A missing or unreadable replay store is fail-closed.

Gate: exact rollback checkpoint and clean before/after state comparison.

### C — Source-bound MacBook ingress

The adapter must authenticate the existing MacBook administration identity,
derive the client fingerprint from that authenticated SSH session, verify the
pinned Proxmox host key, create the manifest from live preflight values, and
pass only the fixed admission envelope to the in-guest wrapper.
It must reject arbitrary URL/model/path/command fields, stale generations,
host-key drift, source/profile drift, and requests after the lease expiry.
The API key remains in LXC110 and is never returned to the MacBook.

Gate: disposable transport tests show accepted matching requests and rejection
of every drift class; no production ingress or firewall change is made.

The slow F2 source chain is a separate preflight concern. Its source-only
snapshot candidate is documented in
`F2-PREFLIGHT-SNAPSHOT-SOURCE-REVIEW-20261019.md`; it must complete before a
narrow final freshness/exclusion guard, and it does not itself establish F2
content integrity.

### D — Persistent supervisor and independent recovery

Install only after the existing manual `local-ai-lease` path is shown to share
the same exclusion or to refuse while the durable cooperative marker exists.
The supervisor holds the lock across preflight, drain, workload and restore.
An independent guardian may terminate the exact owner scope and run restore,
but may not restart workload, extend deadlines, or clear uncertain state.

Gate: target-Linux dry-run proves owner loss, stale heartbeat, cutoff,
identity drift, failed restore, and missing News margin all retain or restore
the lock exactly as specified. No recurring timer is enabled yet.

### E — One attended 30+15 evidence run

Freshly verify MacBook custody, next News ingest, backup proof, accepted
runtime hashes, GPU occupancy and the admission manifest. Run exactly 30
minutes of fixed known-consumer drain plus workload and 15 minutes of restore.
The operator remains on the verified administration path throughout.

Gate: source-bound request receipt, occupancy before/during/after evidence,
independent recovery evidence, exact service/timer restoration, and no
unlisted GPU consumer. A failure retains the lock and is not reported as a
successful lab session.

### F — Scheduled lab admission

Only after E passes may a separate review consider a scheduled admission
window. The schedule must generate a fresh source-bound manifest at start,
recheck the News margin, and refuse admission when MacBook custody or any
hash/consumer/GPU gate is absent. Scheduling is not permission to claim
host-wide exclusivity or to bypass the manual recovery path.

## Remaining approvals and exclusions

The currently installed repair clears only the local Proxmox backup-source
gate. It does not install this admission module, make the MacBook route an
admission boundary, enable a supervisor/guardian, stop Aster services, or
authorize the live 30+15 run. Any target write, service change, schedule,
firewall rule, credential operation, or remote Git push requires its own
approval under the Stream A and platform controls.
