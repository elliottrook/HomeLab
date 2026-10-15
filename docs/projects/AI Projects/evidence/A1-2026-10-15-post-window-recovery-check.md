# October 15 Stream A post-window recovery check

Status: **NO DRILL RAN; full-stop recovery remains unproven and NO-GO.** This
is the one-time 03:40 Vancouver read-only check. It neither executes a
recovery action nor admits an A1 model batch. The earlier [current-cycle
preflight](A1-2026-10-15-read-only-preflight.md) records the backup chain,
partial integrity scan and matching A1 protected subset.

At 03:42–03:45 PDT, `local-ai-lease status` returned `ready`. The
full-stop watchdog timer was disabled/inactive and its service had no active
entry timestamp. A bounded file inventory under `/var/lib/local-ai-lab/`
found only the historical October 12 checkpoint and an October 14 runtime
manifest; the fixed `lease.json` and `lease.lock` paths were absent, as was a
retained archive-integrity receipt directory.
The installed `/usr/local/sbin/local-ai-lease` hash remained
`f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`.
Its `acquire --light` writer still emits `mode: light-service-drain` and a
service list, rather than the installed recovery executor's strict
`AdmissionRecord` schema. The executor, watchdog service and timer retained
their pinned hashes `d75ddfae…`, `3041ed62…` and `9f09de46…`. This is the
previous incompatibility, not a tested compatible installation.

Production `aster-agent.service` (LXC104), `aster-llama.service` (LXC110)
and `aster-speech.service` (LXC116) all reported active, zero systemd
restarts, and active-entry timestamps from October 13 or earlier. These
timestamps and the absent current lease/receipt are consistent with **no
full-stop stop/restart in this window**; process status alone is not a
recovery proof. The A1 sidecar and application watchdog/heartbeat timers
were inactive. No A1 model call was made by this check.

The accepted LXC110 unit SHA-256 was
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`;
the serving SYCL binary was
`0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`.
The resolved 5,627,044,256-byte Qwen3.5-9B Q4_K_M model hashed to
`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`.
The guest still exposed `/dev/dri/renderD128`. The configured LAN endpoint
returned HTTP 200 for `/health` and HTTP 401 for an unauthenticated
`/v1/models` request. The initial localhost probe returned connection refused
because this service binds its LAN address; it was not treated as a failure.
No authenticated generation was attempted, so this check does not prove
post-recovery model correctness, GPU offload or throughput.

The enabled Proxmox all-guest backup remained scheduled at 00:30. TrueNAS
tasks 1, 3 and 2 remained enabled at 01:00, 02:00 and 03:00 and retained
current-cycle `SUCCESS` jobs. The LXC114 News timer remained enabled/active
with `OnCalendar=*-*-* 06,17:15:00 Etc/GMT+7`. These are unchanged
schedule observations, not proof that a full-stop drill restored them.
No complete current-cycle LXC110/116 archive scan or trusted root-owned
integrity receipt emerged after the earlier interrupted check. The live
full-stop card therefore stays **NO-GO** on both measured blockers:
incompatible installed acquisition and missing source-bound integrity.
A1 remains **NO-GO** on its separate application lease, test ingress and
authenticated admission gates; it cannot share a full-stop cycle. The
obsolete evening model runner was not enabled by Stream A.

The one-time 03:40 heartbeat was paused after this check. Continue offline
integration and independent target-Linux verification, then freeze a revised
card and seek distinct live approval for a later backup cycle. Do not infer
completion from this postcheck or from scheduled backup success.
