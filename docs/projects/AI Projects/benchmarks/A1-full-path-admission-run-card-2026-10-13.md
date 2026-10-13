# A1 full Aster-path benchmark admission card

**State: BLOCKED, no model call admitted.** This is the owner-side, headless
synthetic Aster-path card requested by the B60 checkpoint at
`57c551e3671e674d37e9ced5a1d534536e46a8e1`. It does not measure native
Companion display, grant a tool, start a lease, enable a schedule, or promote a
model. The [offline consistency checker](../../../../scripts/aster-adaptive/full_path_admission.py)
has no transport or authority. A passing checker result is still subject to
live source authentication and the platform controller's admission.

## Decision and sequence

First prove that a **test-only** Aster gateway can accept the 20 fictional A1
v2 requests with no tools, emit one opaque observation ID per request, and
bind an actual final headless display/failure event to the gateway record.
The first platform controller candidate stopped `aster-agent.service` in LXC
104 when acquiring a lease. That cannot measure the Aster gateway path.
Before a live card is READY, choose and test one explicit topology: either an
isolated, restricted Aster test instance stays available while the production
service is drained, or a separately reviewed light lease preserves the
gateway while preventing competing inference work. The control and candidate
must use the **same declared gateway boundary**; otherwise a timing delta
confounds model and topology changes. A direct llama.cpp call is useful as a
backend control, never as the full-path result.
The first run uses the accepted 9B/SYCL control profile. A named candidate is
a separate, pinned run only after its model/runtime/endpoint exists and the
same boundary has passed. One profile per card and lease by default: two
20-call profiles cannot be presumed to fit the same after-backup window.
The existing 9B direct-backend median is historical and cannot substitute for
a new Aster-path control. A paired comparison is development regression
evidence, not route qualification without independent labels and class floors.

## Frozen request and output boundary

The Mini retains the 20-case `cases.jsonl` in owner-only custody, SHA-256
`8c5293382a457cbcf4f9999a8904820d6b1d126477fbfc6b672b41a87b62cab9`.
Use the exact frozen order, all 20 rows, one attempt each, no retry of an
uncertain call, no connected tools, LAN-only egress and test-scoped auth. The
hidden key and earlier answers never enter the request path. Freeze one model
profile, Aster gateway/test-adapter profile, scorer, accepted SYCL restore
manifest, and candidate ID by SHA-256 before case one. Record reasoning mode,
temperature 0, output cap 256, a maximum 60 seconds per request, and a
20-minute batch cap. A materially different reasoning/output policy is a new
profile and comparison, never a quiet edit to this card.
The owner-only attempt journal keeps its earlier 900-second default; this
full-path card must pass `max_wall_s=1200` explicitly, and a shorter live
lease deadline still wins. The offline journal now accepts that explicit
cap without changing the historical direct-backend profile.
The [offline Aster request serializer](../../../../scripts/aster-adaptive/aster_full_path_request.py)
constructs one non-streaming `sysadmin` chat request per frozen case with
`enabled_tools: []`, temperature zero and a 256-token cap. It rejects extra
case fields so hidden labels cannot enter the request. This is not a live
client or a server-side tool boundary: the isolated gateway must enforce the
no-tool scope independently, because a client flag alone is not authority.
An [offline ASGI guard candidate](../../../../scripts/aster-adaptive/a1_test_gateway.py)
now rejects every other HTTP route, method, credential or request shape before
the wrapped app. It also requires a set of exactly 20 pinned serialized-request
hashes derived in owner custody from the frozen case file; a well-formed but
unlisted request is rejected. Those hashes do not replace the case-file hash
or an independent server-side no-tool enforcement check. The guard is **not**
a deployed test server or a privileged-tool
revocation: a later isolated instance must use a dedicated test credential,
restricted OS identity, no privileged mounts, reviewed LAN egress and the
same guard/configuration for control and challenger. Its unit tests use a fake
wrapped app, not a real Aster service or B60 endpoint.
An additional in-process fixture joins the guarded request, Aster ASGI
observation ID and client clock; it records a censored request when gateway
completion is not followed by headless display. This verifies the wiring only.

The headless client begins its clock at request acceptance and marks display
only after its final response renderer completes. The Aster ASGI clock emits
the same opaque observation ID and final-body status. The join retains
timeouts, failures and a completed server response that never displayed as
**censored**. It does not infer useful-answer time; that requires later
backend-blind review of sealed owner-only answers. Raw requests, answers,
credentials, arbitrary errors and hidden reasoning do not enter shared timing
records. An isolated/test-only gateway must be source-pinned and must leave
the household production route unchanged. No existing live Aster service is
assumed to satisfy that requirement merely because an offline ASGI fixture
passed.

## Exact live admission gates

The platform owner must supply an authenticated, current host-controller
receipt with lease ID, owner `aster-stream-a`, issued/expiry time, durable
host lock and no-new-start guard. It must bind the same-night backup receipt
and the accepted Q4_K_M model/SYCL backend identities. A separately owned
Proxmox watchdog must be armed to the **same lease ID and generation** and
have a deadline before 04:15 Vancouver,
independent of the Mini, this chat and the candidate process. The same-night
Proxmox archive and TrueNAS guest, LXC 110 and Mac pulls require source-bound
completion/integrity receipts; configured times alone are insufficient.
News and other inference consumers must be quiesced, not merely unobserved.
The test gateway must prove its endpoint, disabled tools, LAN-only egress,
test auth and exact model/gateway/scorer pins. The accepted 9B/SYCL
service uses the pinned Qwen3.5-9B **Q4_K_M model file** and the b11429
**SYCL FP16 build**; these describe different artifacts and are not competing
claims. Its model file, runtime binary, unit, device placement,
authentication and scheduled work must have an
exact restoration manifest and independent postcheck. The owner-only evidence
directory must be new, empty, writable and protected before any request.

Immediately before case one, re-query volatile host, consumer, endpoint,
lease and watchdog state. The offline checker enforces a **minimum 15-minute
restoration reserve**: current time plus the whole 20-minute batch cap and
that reserve must fit before the lease expiry, watchdog deadline and 04:15,
whichever is earliest. A failed or unavailable gate is **BLOCKED with zero
model calls**. Stop on first unexpected response, health regression, drift,
backup/News conflict, lease loss or evidence-write failure. The platform may
require a larger recovery reserve after its live drill; 15 minutes is a
lower bound, not a tested host-reboot guarantee. Preserve the partial journal
and do not retry uncertain work. On release, require an
independent exact SYCL/device/auth response check plus the Aster, Speech,
News and schedule postchecks before clearing the host lock. A unit reporting
`active` is insufficient.

## Verified current state and remaining work

Read-only checks on 2026-10-13 Vancouver found Proxmox backup enabled at
00:30 (job `backup-49999802-1365`) and TrueNAS **rsynctasks** 1/3/2 enabled
at 01:00/02:00/03:00. These
are configured schedules, not tonight's completion proof. The installed
`/usr/local/sbin/local-ai-lease` matches the platform checkout's old
light-only controller SHA-256
`f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`.
It reported `ready` with no state file or lock; no enabled lab/watchdog timer
or B60 launch agent was observed. The obsolete B60 evening runner remains
prohibited. The platform owner has been asked to integrate and live-test
receipt-bound admission,
expiry, independent recovery, consumer isolation and exact restoration from
the B60 recovery candidate. No live failure/reentry proof, staged test-only
Aster gateway or candidate profile has yet been received in this lane.

A separate read-only production snapshot on 2026-10-13 found LXC 110
`aster-llama.service` active with zero restarts, unit SHA-256
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`,
and serving binary SHA-256
`0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`.
The unit selects the Q4_K_M model, Level Zero/SYCL build, 8K single slot and
reasoning off; LXC 104 `aster-agent.service` was also active with zero
restarts. This is a **pre-lease baseline only**. A post-recovery check must
compare against freshly verified model artifact, unit, binary, GPU placement,
authenticated generation and schedule receipts; service-active alone is not
exact restoration.
LXC 114's enabled `news-aggregator-digest.timer` was also read directly;
its `OnCalendar=*-*-* 06,17:15:00 Etc/GMT+7` means 06:15 and 17:15 at
the project's fixed UTC-7 local offset. Its older description/comment still
mentions 06:00/18:00 and must not be used as the restoration target. The
post-lease schedule proof must include this News timer and the four backup
jobs' enabled state and exact schedules, not merely a tuple of clock labels.

The Stream A exclusive wake-up has been moved from its obsolete 01:30 timing
to a **paused 03:15 readiness-check slot**. It remains paused, and even if
later resumed must verify actual backup completion and all gates; time alone
never starts a test. Its 04:15 end and the later analysis/News reservations
remain protected. The continuous offline lane is unaffected.

Before this card can be marked READY, pin the platform implementation and live
recovery receipts, the actual test gateway/endpoint and auth boundary, the
named profile and accepted-restoration manifest, source adapters for the
checker, and a reviewed protected-output path. Then run the synthetic gateway
and display join under the admitted lease, retain failures and restoration
evidence, and decide separately whether a paired candidate or fresh
qualification corpus is justified. Do not revive the obsolete coordinator.
