# A1 isolated Aster process contract

**Proposal, not deployment authority.** Owner: Stream A for the assistant
workload; platform owner for the application-benchmark lease and observer. The October 15
03:15 platform drill is recovery-only. A1 full-path model calls remain blocked
until this sidecar has its own installation, denial and recovery evidence.

## Why this is needed

The current whole-host lease stops production `aster-agent.service` in LXC 104,
`aster-llama.service` in LXC 110, and `aster-speech.service` in LXC 116. A direct
llama.cpp request during that lease measures the backend, not the Aster path.
More directly, the accepted backend is stopped, so an isolated sidecar cannot
call it. A full-path run needs a separate **application-only benchmark lease**
that keeps accepted LXC 110 inference active but exclusively reserved, drains
production Aster/Speech and other consumers, and has its own watchdog and
restoration contract. The full-stop recovery receipt cannot be relabelled.
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
Repeat-body, wrong-inner-key and missing-journal probes must use disposable
probe instances/custody. They must not consume one of the final 20 run's
create-once request claims or alter its credential/configuration after
admission. A failed connection to production Aster while that service is
stopped is not proof of network denial; test the egress policy against an
actually reachable denied destination or a policy-level observation.

The trusted host receipt must name the sidecar exception and bind it to lease
ID/generation, backup receipt, watchdog deadline and source hashes. Stream A
will consume a validated, content-free export; it will not manufacture a
host-owned lease receipt from a dictionary. If the observer cannot attest the
sidecar and its network isolation, keep the A1 card BLOCKED and retain the
direct-backend result as a separate baseline.
The deployment review must compare secret digests locally, without printing
values, to prove none of the sidecar's ingress, inner and backend keys equals
the corresponding production key or either other test key. A dedicated UID
and absence of the production environment file must be observed on the live
process; a source-level environment check alone cannot prove that separation.
The accepted llama.cpp service currently reads an API-key file in LXC 110.
A newly generated sidecar backend key will not work merely because it is
placed in the sidecar environment. The application-lease run card must choose
and prove a reversible authentication path: a specifically reviewed addition
and reload of a test-only key in LXC 110, or an independently isolated
credential-translating proxy. Reusing the production key in the sidecar is
not an implicit fallback. No live A1 installation is ready until this is
resolved and included in the restoration manifest.
The offline [`a1_isolated_app.py`](../../../../scripts/aster-adaptive/a1_isolated_app.py)
factory refuses root, unpinned backend/output/tool/deadline settings,
privileged env values and absent owner-only journal/clock custody before it
imports Aster. It then composes the strict request guard around the actual
Aster ASGI app. Its fixture tests use a fake inner app: they prove assembly and
fail-closed configuration only, not a live LXC process, network isolation or
production Aster behavior. A distinct UID, unit and network denial test remain
deployment prerequisites.
The offline Stream A admission schema is now `aster-full-path-admission.v2`:
it requires a separate `sidecar` observation from `platform-host-controller`,
matching lease ID/generation and pinned source digest, and explicit true
observations for distinct UID, one worker, test port, credential denial,
network denial and start within the lease. A gateway's own assertion cannot
substitute for this host observation. This is still a shape/consistency check,
not authentication of the host source.
It also rejects the full-stop recovery lease: the application-benchmark scope,
active and exclusively claimed backend, and production Aster/Speech quiescence
must all be independently attested.
Because the application lease temporarily changes the LXC 110 ingress policy
and adds a test API key, its independent watchdog must attest the ability to
stop the sidecar, restore the prior ingress policy, remove the test key and
reload/revalidate production authentication, then restore production
consumers. Merely restarting Aster/Speech leaves the backend security boundary
changed. The offline v2 checker requires these distinct watchdog observations;
live effects and restoration still need an expiry-driven drill.

For the first full-path run, use the accepted 9B/SYCL control only, 20 frozen
fictional requests, one attempt per request, maximum 10-minute batch and
15-minute minimum restoration reserve before 04:15 Vancouver. Preserve
uncertain outcomes and stop on the first surprising response or host change.
The control is regression evidence, not automatic route promotion.

## Platform candidate source review — 2026-10-14

The platform owner's local `df7b6bb2` candidate added ordered application
watchdog actions. A source review of its controller and watchdog found three
unclosed live gates: `acquire()` validates a post-start sidecar observation
before the lease can exist; `controller.restore()` can restart Aster/Speech
without clearing the sidecar, temporary LXC 110 ingress rule or test key; and
the watchdog has no persisted per-effect attempt reconciliation or verified
deadline. A process interruption could therefore replay a key/backend effect
or leave production consumers running under a changed backend boundary.
These are **source-candidate findings**, not observed production faults. The
platform owner has been asked to split pre-lease and post-acquire receipts,
remove the bypass restore path, and add no-blind-replay recovery tests. The
A1 installation/run card remains **BLOCKED** until the corrected code, fixed
host helpers and a live recovery drill are independently checked.

**Further host/key review:** A read-only LXC 110 `stat` on 2026-10-14 found
the live `/etc/aster-llama-api-keys` file owned by `ollama:ollama`, mode `0600`.
The platform run card's root-owned description is wrong. Its offline key
helper also replaced the pre-add checkpoint during removal, and allowed
overwriting a pre-existing checkpoint on append. These are candidate-source
faults, not evidence of a live key change. The owner has been asked to retain
the original checkpoint create-once, preserve exact live file metadata and
test interrupted add/remove recovery before any LXC 110 mutation.

**Source correction and remaining effect gap:** Platform commits `e5281c58`
and `2ebfd6ce` corrected the stale acquire rollback references, added an arm
transition and late recovery, and changed the key helper to preserve the
`ollama:ollama` 0600 metadata and a create-once pre-add checkpoint. These are
offline corrections with fixture coverage, not host recovery evidence. The
controller still stops production consumers before `arm()`, while the watchdog
refuses to recover an unarmed persisted lease. The run card also changes the
LXC 110 key file and restarts llama.cpp before acquiring any application
lease. A crash in either interval could leave an effect without the promised
independent recovery path. The platform owner has been asked to cover every
effect from its first mutation with a persisted, timer-recoverable state and
failure-injection tests. Keep A1 live admission **BLOCKED** until that order,
the fixed host helpers and live restore are independently verified.

Platform commit `8f70d330` moved the armed state write before consumer stop.
The next independent review found two still-open ordering conditions: its
pre-lease input requires `exclusive_backend_claim=true` before the run card
applies and verifies the temporary exclusive ingress policy, and its watchdog
unconditionally restores the ingress/key checkpoints even if recovery starts
before those checkpoints were created. The receipt must distinguish a planned
claim from a host-observed exclusive claim, and recovery must distinguish an
effect never started from an uncertain effect. Failure injection at each
transition is required before live admission.

An exact-file check also found the current Stream A `a1_headless_client.py`
SHA-256 `beabc81ad44d205bc908c248f2fea50fb12faaac01f654a160712a550aa3fbc2`
differs from the platform installation manifest's older pinned hash. The
three other Stream A files in that manifest matched. The manifest must be
repinned to an explicitly reviewed source commit before a copy or start.

**Read-only host preflight, 2026-10-14:** LXC 104 reports systemd 257,
`aster-agent.service` active, no `aster-a1-test.service`, no
`aster-a1-test` account and no listener on TCP 19104. LXC 110 reports
`aster-llama.service` active; its current `inet filter` input chain has policy
`accept` and no rules. LXC 116 reports `aster-speech.service` active. This
confirms that the sidecar and temporary ingress restriction are not yet
deployed; it does not establish lease admission, network isolation or
backend exclusivity. The proposed ingress helper must add and later remove a
precisely scoped rule while preserving this observed baseline.

**Ingress helper candidate review:** Platform commit `279bdef3` adds an
offline, handle-bound LXC 110 nftables helper. A read-only `nft -j -s` query
confirmed that its exact empty-chain fixture matches the current live input
chain; `ss` showed llama.cpp listening on IPv4 `192.168.70.12:11435` only.
No rule was applied. Before deployment, the helper must durably fsync its
checkpoint directory after atomic replacement and verify the tagged rule's
full family/table/chain/match/action before deleting by handle. A matching
comment alone is not sufficient. The live observer must recheck the IPv4-only
listener, because the proposed IPv4 source rule would not exclude IPv6 if the
backend later listens there. These findings were sent to the platform owner;
the test remains blocked pending correction and effect-level recovery proof.
