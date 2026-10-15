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
104 when acquiring a lease. The installed whole-host recovery lease also stops
`aster-llama.service` in LXC 110, so it cannot run the accepted B60/SYCL
backend either. **That lease is for recovery drilling, not this benchmark.**
Before a live card is READY, choose and test one explicit topology: either an
isolated, restricted Aster test instance stays available while the production
service is drained **under a separate application-only benchmark lease that
keeps the accepted backend active and exclusively claimed**, or a separately
reviewed equivalent topology with its own recovery contract. The control and candidate
must use the **same declared gateway boundary**; otherwise a timing delta
confounds model and topology changes. A direct llama.cpp call is useful as a
backend control, never as the full-path result.
The first full-path control has its own pinned
[`a1-full-path-9b-candidate-profile-v1.json`](a1-full-path-9b-candidate-profile-v1.json),
SHA-256 `7caddc30074f5925722861c59f70733894037b9fc5b0865feb98bf9e08bbbfec`.
This newer pin includes the corrected credential/import boundary, production-
matched wheel hashes and rebuilt source archive. Earlier `a5290a8c…` and
`af29955f…` profile pins are superseded; do not combine their source bundles
or runtime receipts with this run.
It is a Stream A candidate-path baseline. The prior direct-backend A1 v2
profile has a 600-second batch cap and a different prompt path; it must not
be reused or described as the same full-path profile.
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
The offline [`a1_full_path_capture.py`](../../../../scripts/aster-adaptive/a1_full_path_capture.py)
now composes the existing one-attempt private answer journal with a separate
owner-only, content-free client-clock file. It records a censored clock and
stops after an uncertain transport or invalid output. The 33 focused A1
fixtures passed on 2026-10-14; they open no network socket and do not
authenticate a lease. The platform-supplied caller must still validate live
admission immediately before supplying the actual client transport.
The candidate gateway/factory were repinned after a deployment-layout check
found that their old source-relative Git-root constant would resolve to `/`
under `/opt/aster-a1-test`, rejecting every durable evidence directory.
They now detect actual `.git` ancestry instead; the focused fixture suite
passes in a temporary non-Git layout. This source correction changes the
profile hash above and invalidates the earlier `f97644b3…` pin.

## Exact live admission gates

The platform owner must supply an authenticated, current host-controller
receipt with lease ID, owner `aster-stream-a`, issued/expiry time, durable
host lock and no-new-start guard. Its scope must be
`aster-app-benchmark`, not the full-stop recovery drill; it must attest that
the accepted backend remains active and is exclusively reserved for the
admitted sidecar while production Aster, Speech, News and other consumers are
quiesced. The independent watchdog must use this same scope and restore the
normal consumers without treating the preserved backend as a stopped unit.
The lease must bind the same-night backup receipt
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
The offline consistency checker is now `aster-full-path-admission.v2` and
rejects a full-stop lease or an inactive/unclaimed backend even if its
model/version strings match. Its synthetic tests do not create the separate
host lease or prove live exclusivity.

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

The isolated sidecar's Python dependency set has a local, production-version
matched wheelhouse candidate. Its 34 wheel filenames and SHA-256 hashes are
recorded in
[`a1-production-matched-wheelhouse-manifest-2026-10-14.json`](a1-production-matched-wheelhouse-manifest-2026-10-14.json).
The manifest itself hashes to
`0fb7f44e2c856736ab741b23a70f28fa69dbd95a2eadad6c6d8d1b4416acadee`.
All versions match the read-only package inventory of the live LXC 104 Aster
virtual environment, excluding pip; an offline `pip download --no-index`
resolution of the six declared requirements succeeds for Linux CPython 3.13
x86_64. The `http_ece` wheel was copied read-only from that environment's
pip cache with matching remote/local hash; the remaining wheels were
downloaded locally. This is dependency preparation, **not** proof that the
sidecar starts or that its dependency closure is independently qualified.
The wheel files currently reside outside Git in
`/private/tmp/aster-a1-prod-wheelhouse`; their hashes must be checked again
before any supervised installation. A temporary directory is not durable
custody or an installation receipt.

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
The B60 recovery candidate probes each unit before starting it and refuses an
uncertain prior start. The platform owner's developing adapter must retain
that no-blind-replay behavior as well as a fresh exact post-start check; an
offline green suite or a `systemctl start` exit is not a recovery receipt.

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
An additional read-only LXC 110 check on 2026-10-13 resolved the GGUF symlink
to a 5,627,044,256-byte Ollama blob and computed SHA-256
`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`,
matching the repository's accepted model pin. The remote hash command took
about 18 seconds including SSH; a universal five-second observer timeout
cannot be used for this full-file check. This is a pre-lease integrity
observation, not a post-recovery receipt.
The proposed Proxmox-side TrueNAS batch SSH schedule probe failed with
`Host key verification failed`; Proxmox root had no matching known-host entry.
The TrueNAS ED25519 fingerprint obtained through the Mini's authenticated
existing SSH path matched a Proxmox-side scan
(`SHA256:QBtPEVZCzn5suuM98WY2bGSSvdgOLZ5xpLd17Xu0Xbo`). No host key was
enrolled and no new TrueNAS access was granted. The platform owner must either
stage a reviewed pinned-host-key, least-privilege read path or leave remote
schedule verification UNKNOWN while independent recovery restores local
production and retains the lease lock. Disabling host-key checks is not an
acceptable shortcut.
The platform owner's local recovery candidate later added an allowlisted
effect runner and a disabled systemd executor. Stream A's independent source
review still found two unproven cases: the first executor revision would hash
the 5.6 GB model on every one-minute tick during a healthy lab lease, and an
interrupted persisted `RESTORING` state could yield `FAILED` before an effect
attempt. The proposed attended drill also barred timer activation, so it
would not prove timer-driven independent recovery. These are review findings
on an **uninstalled local candidate**, not observed production incidents.
Live admission remains BLOCKED until corrected code, fault tests and a
bounded timer-enabled recovery drill are reviewed and authorized.
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
The [isolated Aster topology candidate](A1-isolated-Aster-topology-2026-10-13.md)
defines the proposed path and its separate installation review gate.
The [fixed sidecar contract](A1-isolated-process-contract-2026-10-14.md)
specifies the process, credential, network, observer and denial evidence needed
before that path can be admitted. The platform owner confirmed the current
lease observer cannot treat an arbitrary second LXC 104 process as quiescent;
the October 15 recovery drill therefore does not itself admit A1 calls.

The offline gateway candidate now derives its 20 allowlisted body digests from
the validated sealed corpus using the same serializer as the client. Only
digests, never request text or labels, belong in its configuration. It rejects
an attempted repeat before forwarding and strips its ingress credential from
the downstream ASGI scope. The current Aster endpoint requires authentication,
so an isolated test instance must use a distinct, test-only inner credential;
the guard can substitute that credential after admitting the request. Neither
the production Aster key nor the ingress test key should be reused for this
inner role. An owner-only, create-once digest journal
survives gateway reconstruction in an isolated test. The offline gateway now
refuses construction without that journal and a distinct inner bearer; 32
focused gateway, clock, request and admission tests pass. A live deployment must
configure the journal on durable protected storage and verify its ownership,
restart behavior, single-worker boundary and rollback before READY. In-memory
mode alone is insufficient. The gateway is not deployed; no current Aster
request has passed through it.
The offline headless client adapter uses the same frozen serializer, permits
only a literal loopback/RFC1918 test endpoint, makes one POST without redirect
or retry, bounds the response, and requires a terminal answer plus opaque
observation ID. It returns raw fictional answer text only to the owner-held
capture caller and a separate content-free client clock. Transport and parse
failures carry a censored content-free clock on the raised error, so a later
owner-held runner can retain failed attempts without treating them as slow
successes. The adapter does not obtain a
lease, open a socket when imported, persist evidence, or make the card READY.
Four synthetic transport tests cover this boundary; the combined focused
gateway/admission/request/client suite passes 36 tests. The source-bound live
preflight and protected journal must still surround its use.
The offline guard also rejects nonempty query strings and forwards only its
validated content type and distinct inner bearer to the wrapped app. This
prevents caller-supplied cookie, identity/proxy or tool headers from crossing
the test boundary. Synthetic tests cover those cases; the check does not
replace the isolated instance's OS, credential and egress controls.
The offline preflight now explicitly rejects an observed gateway without a
durable attempt journal, distinct inner authentication, the pinned 20-request
set and a common Aster gateway topology for control and challenger. These
reported observations still require independent live-source proof; a passing
dictionary check is not authority to start the run.

**2026-10-14 Vancouver live recheck:** The installed Proxmox controller still
reports `ready` and has SHA-256
`f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`;
the checked watchdog units were absent/inactive. The platform owner is doing a
separate read-only snapshot and has been asked to complete the platform-owned
installation and recovery drill. No lease or model call was started. The A1
card remains **BLOCKED** until those live receipts and an isolated Aster test
endpoint exist; yesterday's scheduled window did not satisfy admission.

**Independent recovery review, 2026-10-13:** The platform owner corrected
healthy watchdog ticks so unmeasured service, GPU, schedule, model, unit and
authentication checks are `UNKNOWN`, not passes. A subsequent source review
found that set-based journal matching could hide a repeated unfinished start
and a historical start record could suppress a current service probe. The
owner's local `49014703` revision makes intent matching attempt-aware, probes
each service again, and passes 44 offline tests. This is a reviewed **local
candidate**, not an installed watchdog or live recovery result. A fresh
read-only Proxmox check still finds the watchdog timer and service absent,
the previous light-only controller at SHA-256
`f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23`,
no active lease state/lock, and the accepted LXC 110 service active. The
Stream A 03:15 exclusive automation remains paused. The TrueNAS observer
transport and a source-bound same-night backup receipt remain open; the
obsolete evening runner remains disabled. No full-path model call is admitted.

**Private corpus derivation check, 2026-10-13:** Read only the owner-protected
`cases.jsonl` from the approved A1 v2 backup, validated its pinned source hash
and generated 20 distinct serialized request digests in memory. The SHA-256 of
the sorted digest list joined with `\n` **without a trailing newline** is
`19f1370e3e4a352fa20615504350c34ee38b56e97b010d543b76394934887589`.
No case text, answer key, individual request digest or credential was printed
or put in Git. This establishes deterministic fixture preparation, not a
configured live gateway or an admitted model run.
The same source hash, 20 distinct serialized digests and aggregate were
rechecked read-only on 2026-10-14. No case text or individual digest was
printed. A trailing newline produces a different aggregate and must not be
silently substituted in the final gateway configuration receipt.

**Later read-only transport and admission review, 2026-10-13:** The platform
owner installed a dedicated, constrained TrueNAS observer. Stream A independently
queried its exact pinned Proxmox-to-TrueNAS schedule path: tasks 1, 3 and 2
were enabled at 01:00, 02:00 and 03:00 respectively. This resolves the
earlier host-key/transport blocker for schedule metadata only. It does not
prove that those jobs completed on a given night or that an archive can be
restored. The platform's fixed mirror query and metadata parser are candidate
preflight evidence; filename, size and date-string agreement alone are not
archive integrity or source-bound admission.

Independent source review then demonstrated that a caller-controlled
`authenticated=True` flag could make a fabricated receipt pass the proposed
benchmark gate despite 55 passing unit tests. The platform owner removed that
path in local revision `b6f260c0`; the gate again refuses all Aster benchmark
admission until a trusted execution boundary produces the receipts. Stream A
re-ran the 55 tests against the corrected source. Proxmox still has no installed
watchdog unit/timer or active lease. The next evidence is a bounded integrity
check, a live two-sample consumer-quiescence receipt and an attended recovery
drill; none has been accepted as full-path admission here.

**Backup-chain ordering check, 2026-10-13:** The pinned observer also exposes
per-task job start/finish times. A sanitized read found task 2's most recent
success at about 03:00 Vancouver, while tasks 1 and 3 last succeeded around
11:06 and 11:19 on the same date. Thus matching the local date and a `SUCCESS`
state is insufficient to prove the ordered 01:00/02:00/03:00 overnight chain.
The platform owner was asked to bind each task's start and finish to the
selected Proxmox archive creation, previous task, lease issue and allowed
window. This observation admits no lab run and does not diagnose why those
tasks ran later.

**Follow-up source review, 2026-10-13:** The platform candidate now checks the
latest required artifact creation time, nonoverlapping 1→3→2 completion, and
completion before lease issue. Stream A found that finish-time checks alone
still admitted a pre-slot start; the owner added same-date, no-earlier-than-
slot start checks in local `b75e835c` and pinned the candidate in
`7dc639b5`. Its owner-reported suite now passes 62 tests with two root-custody
tests skipped in the Mac environment. These commits are source evidence, not
a live installed source boundary or an overnight-chain receipt. The current
daytime reruns remain ineligible and A1 remains **BLOCKED**.

**Next overnight metadata observation, 2026-10-14 03:00 Vancouver:** A
read-only Proxmox query found selected-date 104, 110 and 116 archives created
before the TrueNAS pulls. TrueNAS task metadata reported `SUCCESS` for task 1
at 01:00:01–01:06:15, task 3 at 02:00:01–02:06:27, and task 2 at
03:00:01–03:00:02. This is an ordered schedule observation, not an archive
integrity or restored-content receipt. In particular, a one-second Mac task
does not prove that expected Mac files were copied, and the candidate adapter
checks LXC 110 mirror metadata but not the Mac or full guest-pull contents.
The platform owner was asked to keep that distinction in admission. The live
Proxmox watchdog units were still `not-found`/inactive and the installed
controller reported `ready`; no lease or full-path run was admitted.

**Mac receipt implementation review, 2026-10-14:** The platform branch's
`d54dd4cf` adds an offline validator for a content-free Mac tree summary,
with tests, and `c72d10fc` pins its staging manifest. This is useful contract
work, but no fixed-path TrueNAS producer or adapter call currently obtains
that summary. The validator also does not itself bind capture time to task 2's
completion or independently authenticate the producing identity. The platform
owner is preparing the exact restricted observer command and integration before
requesting a new read-only access grant. Until then, task status and the
standalone parser are insufficient for A1 admission. The watchdog and live
recovery gates remain separate blockers.

**Fixed Mac observer candidate review, 2026-10-14:** The platform owner then
wired an exact `aster-mac-pull-summary` command and a local producer in
`5495df6c`, pinned by `5d3d50fe` (69 owner-reported tests, two custody skips).
The producer traverses the full Mac backup tree and hashes file contents. A
nonempty tree and current task-2 `SUCCESS` do not by themselves prove that this
cycle copied the expected Mac content: an unchanged prior tree would also
pass. The full-tree read also needs a measured size/runtime bound and
symlink-race review before a new root-owned observer permission is requested.
Stream A asked the platform owner to either establish a source/destination
manifest for the intended subset or narrow the receipt's claim to tree
presence/integrity. This remains offline candidate code; no observer grant,
lease or A1 model run followed.

**Correction in the platform candidate:** `41ec8030`/`72b96456` removed the
full-file read, bounded the metadata scan to 20 seconds and 100,000 entries,
labels its result `tree-present-only`, and removed it from the backup-admission
digest. The owner reports 69 passing tests and two custody skips. This closes
the earlier overclaim in source, but no current-cycle Mac source/destination
comparison exists. The Mac observer remains uninstalled; its future output
would be diagnostic only, while A1 backup admission and live recovery remain
blocked on their separate gates.

**Disabled sidecar stage, independently checked 2026-10-14 Vancouver:** Jason
approved the exact disabled-install phase. The platform owner staged the
source and 34-wheel dependency set in LXC104 and wrote the content-free
`/var/lib/aster-a1-test/staging-receipt.json` at local commit `64740ea8`.
Stream A then independently observed `aster-a1-test.service` loaded but
disabled/inactive with PID 0, no TCP 19104 listener, no
`/etc/aster-a1-test/runtime.env`, and dedicated UID/GID 1904 with no other
groups. The installed unit and isolated-app SHA-256 values match the approved
card (`949bd266…`, `b634b051…`); the receipt pins the current profile,
source-bundle and wheel-manifest hashes. LXC110 `aster-llama.service` remained
active with zero restarts. This proves a reversible disabled stage, **not** a
live test endpoint or benchmark admission. The application watchdog timer was
still `not-found`, the full-stop watchdog timer remained disabled/inactive,
and the installed controller reported `ready` without an A1 lease. The
20-request full Aster-path benchmark remains **BLOCKED with zero model calls**
pending a separately reviewed application lease, independent recovery,
source-bound backup/consumer receipts, test-only auth/ingress and positive and
negative isolation probes. The 03:15 full-stop drill cannot supply the A1
application lease because it stops the accepted B60 backend.
