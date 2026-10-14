# A1 isolated Aster process contract

**Proposal, not deployment authority.** Owner: Stream A for the assistant
workload; platform owner for the whole-host lease and observer. The October 15
03:15 platform drill is recovery-only. A1 full-path model calls remain blocked
until this sidecar has its own installation, denial and recovery evidence.

## Why this is needed

The current whole-host lease stops production `aster-agent.service` in LXC 104,
`aster-llama.service` in LXC 110, and `aster-speech.service` in LXC 116. A direct
llama.cpp request during that lease measures the backend, not the Aster path.
Leaving an arbitrary second Aster process running would also defeat the
platform observer's current consumer-quiescence claim. The test sidecar must be
an explicit, measured exception; it is never counted as ordinary quiescence.

## Proposed fixed identity and scope

| Property | Required value or proof |
|---|---|
| Process | One named `aster-a1-test.service` in LXC 104, one worker, distinct unprivileged UID with no `aster`, broker, approval or administrative group membership. No launch by a general agent. |
| Code | Exact Aster source and dependency hashes, plus Stream A's guarded gateway, ASGI clock and headless-client hashes. Control and challenger use the same source and gateway topology. |
| Listener | Dedicated, non-public port, distinct from production `:9120`; ingress restricted to the named Mini test client and one ephemeral, test-only bearer. No other Aster route is reachable through this listener. |
| App authority | Frozen 20 request digests, `POST /v1/chat/completions` only, no extra path/query, `enabled_tools: []` enforced before Aster, `ASTER_MAX_TOOL_ROUNDS=0`, no lab targets/workers or broker/approval socket. Test UID cannot read production environment, OpenBao material or privileged mounts. |
| Inner auth | A separate test-only Aster key, distinct from ingress and backend keys. The guard replaces ingress auth with this key. All keys remain out of Git, model input, logs and result exports. |
| Model path | Explicit test backend URL/key and exact accepted 9B Q4_K_M/SYCL profile. No default production URL/key fallback. `ASTER_MAX_RESPONSE_TOKENS=256` and `ASTER_REQUEST_TIMEOUT=60`; the current Aster default output cap 160 would silently change the A1 budget. |
| Data | Empty synthetic knowledge/state paths. No household context or production report mounts. Owner-only durable attempt claims and ASGI clocks outside Git, protected before the first request. |
| Network | Demonstrated egress restriction to the named leased backend plus required loopback; no Internet, Authentik, OpenBao, broker, other LAN service or cloud route. Do not assume a systemd sandbox directive works inside the LXC without a denial test. |
| Lifecycle | Installed disabled. Host owner starts it only inside a current source-bound lease, attests UID/process/port/egress and exact source, and stops it before the restoration reserve. Independent watchdog must still restore accepted production if Stream A or the Mini disappears. |

## Admission and denial evidence

Before the first model call, test an unrecognized bearer, another path,
query string, extra tool, changed prompt body, repeated body, second worker,
missing durable journal, wrong inner key, and attempted privileged socket/file
access. Each must fail without a backend call. An allowed fictional request
must carry the same opaque observation ID through Aster's terminal response
and the headless display event. The platform observer must distinguish this
exact admitted sidecar from every other inference consumer and detect an
unexpected start, restart, port, UID or source hash. A source-only unit test
is insufficient.

The trusted host receipt must name the sidecar exception and bind it to lease
ID/generation, backup receipt, watchdog deadline and source hashes. Stream A
will consume a validated, content-free export; it will not manufacture a
host-owned lease receipt from a dictionary. If the observer cannot attest the
sidecar and its network isolation, keep the A1 card BLOCKED and retain the
direct-backend result as a separate baseline.
The offline [`a1_isolated_app.py`](../../../../scripts/aster-adaptive/a1_isolated_app.py)
factory refuses root, unpinned backend/output/tool/deadline settings,
privileged env values and absent owner-only journal/clock custody before it
imports Aster. It then composes the strict request guard around the actual
Aster ASGI app. Its fixture tests use a fake inner app: they prove assembly and
fail-closed configuration only, not a live LXC process, network isolation or
production Aster behavior. A distinct UID, unit and network denial test remain
deployment prerequisites.
The offline Stream A admission schema is now `aster-full-path-admission.v1`:
it requires a separate `sidecar` observation from `platform-host-controller`,
matching lease ID/generation and pinned source digest, and explicit true
observations for distinct UID, one worker, test port, credential denial,
network denial and start within the lease. A gateway's own assertion cannot
substitute for this host observation. This is still a shape/consistency check,
not authentication of the host source.

For the first full-path run, use the accepted 9B/SYCL control only, 20 frozen
fictional requests, one attempt per request, maximum 10-minute batch and
15-minute minimum restoration reserve before 04:15 Vancouver. Preserve
uncertain outcomes and stop on the first surprising response or host change.
The control is regression evidence, not automatic route promotion.
