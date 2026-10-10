# Research log — 2026-09-25

## 2026-10-09 — Same-signer update exposed legacy Keychain ACL problem

The stable-signed version 11 opened normally after Jason's one-time
`Always Allow` and twice restarted without a prompt. A real version-12 update
retained the same designated requirement and passed mutual code-requirement
checks, but prompted again for the existing Companion saved-login item. Jason
provided the exact prompt screenshot. Keychain Access showed five separate
`AsterCompanion.app` trusted entries on `oidc_session_v2`; all-app access was
off. This fails the update-continuity gate. Version 11 was restored and again
opened signed in without a prompt. A local version-13 candidate can copy the
session once to a newly created Companion-only item while retaining the old
item for rollback; all 52 synthetic Companion tests and the signed build pass.
No real token migration has run. See the [finding and next gate](evidence/D3-native-stable-signing-keychain-design-2026-10-09.md).

## 2026-10-09 — Stable-signed Companion installed; first launch pending

After Jason completed macOS trust authorization, the new Aster certificate
became a valid code-signing identity with user-domain CodeSigning-only trust.
Two disposable app variants with different versions and code hashes passed
strict signature checks and had an identical certificate-based designated
requirement. The build script then produced a stable-signed candidate. The
prior installed app was verified and preserved; the stable-signed app replaced
it and passed signature verification. Its first launch is waiting at the
existing saved-login Keychain transition or another startup block; Jason was
asked to resolve only an exact Companion prompt or report no prompt. Normal
mode and repeat-prompt behavior are still unverified. See the [signing evidence](evidence/D3-native-stable-signing-keychain-design-2026-10-09.md).

## 2026-10-09 — Companion signer created; trust gate pending

After Jason's explicit approval, Certificate Assistant created an owner-held
code-signing certificate and private key in the Mac login Keychain. The
certificate has code-signing-only extended key usage; no private key was
exported. The attempted user-domain, code-signing-only trust setting has not
completed macOS authorization: `security find-identity` still reports zero
valid signing identities. No two-build signing test or installed-app replacement
has run. The current Companion remains operational with its prior ad-hoc
signature. See the [implementation checkpoint](evidence/D3-native-stable-signing-keychain-design-2026-10-09.md).

## 2026-10-09 — Installed Companion repair and repeat Keychain prompt

Jason approved installation of the refresh/recovery repair. The new signed
Companion opened its normal composer after one saved-login Keychain prompt;
AI-PAM showed no pending approvals, ordinary Codex intake remained closed,
and the installed helper recovered all twelve exact completed turns read-only
without new model or tool actions. Natural token refresh has not yet been
observed, so the refresh fix is not fully validated. The installed app remains
ad-hoc signed. Its designated requirement differs from the previous build,
which explains why a first-launch item-access prompt returned after replacement.
The prior refresh fix removed an additional read but did not solve identity
continuity across app updates. The [stable-signing design and test gate](evidence/D3-native-stable-signing-keychain-design-2026-10-09.md)
records a narrowly scoped proposed remedy; no persistent signer or Keychain
trust change has been made. The [replacement record](evidence/D3-native-refresh-and-recovery-replacement-gate-2026-10-09.md)
retains the installed validation and remaining limits.

## 2026-10-09 — Fixed native set complete; D3 routine release held

After Jason accepted the exact fictional cases and candidate labels, Companion
completed cases 2–12 with one reviewed send each. The content-free journal now
has twelve distinct completed case turns. Visible answers provisionally met
all frozen properties; read-only inspection found zero tool items. Median
send-to-result time was 4.41s across twelve samples. This is not a reliability
rate or proof of sysadmin capability. Five turns contained internal reasoning
items that the then-installed read-only recovery helper rejected. A local fix,
subsequently installed as recorded above, accepts those items without exposing
them or accepting tools; all twelve historical turns then replayed read-only.
A separate unnecessary Keychain read-back during token refresh stalled
Companion's UI. The installed repair removes that read-back, but live refresh
behavior is unverified. Hold D3
routine release pending independent answer review and restart/refresh/failure
validation. See the [finite-set result](evidence/D3-native-finite-12-result-2026-10-09.md).

## 2026-10-09 — Native case 1 answer recovery after restart

Jason approved a signed Companion recovery build after read-only source review,
six focused bridge tests and 49 native tests. The previous app was preserved
for rollback. Normal signed-in Aster, AI-PAM and closed Codex request intake
opened after a Companion saved-login Keychain prompt. The finite evaluation
view recovered the original completed HTTP 503 answer for case 1, recorded a
content-free `recovered` event, and did not start another model turn or send
case 2. An app-specific Keychain prompt occurred again at evaluation-mode
startup; no worker credential ACL was widened. Independent label review and
authorization for the remaining finite cases are still open. See the
[installation and recovery evidence](evidence/D3-native-original-answer-recovery-candidate-2026-10-09.md).

## 2026-10-08 — Cross-host grouped handoff PASS

Approved exact three-case harness passed over actual SSH/container endpoints:
success, gateway disconnect and Mac sink failure. Each verified fixed fictional
vault revocation and precise journal outcome; all owned peers exited. Removed
enumerated files/receipts from all targets and independently verified absence.
Production AI-PAM remains healthy; no real credential/Keychain/API/account/model
use. Successful primitives are complete; continue human ceremony and real
inactive-provisioning preparation. See
[cross-host result](evidence/D3-cross-host-handoff-gate-2026-10-08.md).

## 2026-10-08 — Complete pipe-chain tests and grouped transport gate

Added fictional endpoint adapters running the real protocol/provisioner in separate
processes. Success, gateway disconnect and Mac sink failure all verify exact stage
outcomes, child exit, source-local revocation receipt and secret-free journals.
211 local tests pass, including all three cases through the complete harness.
Prepared one three-case cross-host SSH/container rehearsal with reviewed immutable
bundle and 10-minute cap. Only read-only staging-path checks performed remotely.
Human ceremony remains closed. See
[cross-host approval scope](evidence/D3-cross-host-handoff-gate-2026-10-08.md).

## 2026-10-08 — Isolated real-engine provisioning PASS

Approved v5 completed with installed OpenBao 2.6.4: fixed configuration verified,
eight prohibited actions denied, fictional credential provisioning completed,
root and scoped-admin revocations confirmed. About 1.067s CPU/66.2 MiB peak RAM.
Removed exact staged files/runtime unit; independent absence and production
health checks passed. No real credentials/authority or model calls. Retain prior
failures; do not rerun this primitive without reason. Resume cross-host handoff
and complete human ceremony integration. See
[attempt 5 result](evidence/D3-scoped-bootstrap-and-isolated-vault-gate-2026-10-08.md).

## 2026-10-08 — Diagnostic isolated network-address comparison mismatch

Approved v4 pinpointed token_bound_cidrs after successful fixed-role creation/read;
fresh fictional root revocation confirmed. Upstream formatting explains /32
versus host-only spelling. Prepared strict network-equivalence comparison with
negative cases for broader/other hosts; 206 tests pass. No authority expansion.
Removed exact fixture/unit; production healthy. v5 isolated confirmation gate
pending; no complete provisioning pass claimed. See
[attempt 4 record](evidence/D3-scoped-bootstrap-and-isolated-vault-gate-2026-10-08.md).

## 2026-10-08 — Narrower fixture failed at bootstrap; diagnostics improved

Approved v3 stopped during bootstrap, before policy denial checks/provisioning.
Cause not established by the coarse fixed stage result. Removed exact fixture
files/unit; production remains healthy. Added allowlisted API method/path/status
and mismatched field-name reporting only, with tests against secret disclosure.
204 local tests pass. v4 diagnostic-only immutable bundle awaits approval; no
authority or isolation changes, no automatic retry. See
[attempt 3 evidence](evidence/D3-scoped-bootstrap-and-isolated-vault-gate-2026-10-08.md).

## 2026-10-08 — Real-engine test rejected provisioning; authority reduced

Corrected isolated attempt reached provisioning after bootstrap/root-revocation
and eight denial checks passed, then failed. Cleaned exact unit/files; production
vault and broker readiness unchanged. Version-pinned ACL source explains required
parameters affecting reads, unlike the original mocks. Reduced temporary-token
authority instead of relaxing constraints: human bootstrap owns fixed config,
ordinary provisioning can only verify it and handle two exact credential paths.
202 tests pass. Prepared immutable v3 isolated-test bundle; approval pending.
See [full evidence and source](evidence/D3-scoped-bootstrap-and-isolated-vault-gate-2026-10-08.md).

## 2026-10-08 — Isolated attempt stopped at source visibility; cleaned

Approved bundle/unit staged and validated, but PrivateTmp hid its /var/tmp source.
Python exited before running tests; no disposable vault was launched. Removed all
approved fixture files/unit and confirmed production vault/AI-PAM remain healthy.
Prepared a source-path-only correction under /opt with all isolation retained,
new immutable archive hash and explicit next-attempt approval gate. No retry or
real credential use. Evidence retained in
[the isolated experiment record](evidence/D3-scoped-bootstrap-and-isolated-vault-gate-2026-10-08.md).

## 2026-10-08 — Scoped bootstrap contract; real-engine isolation gate

Prepared hidden human-terminal bootstrap and exact expiring administrator-token
contract. Root is revoked before delivery of scoped child; unknown outcomes stop.
Added payload constraints to named policy/role writes and tests for broader
authority rejection and failure cleanup. 200 local tests pass. Current official
API pages label 2.7.x, so do not infer 2.6.4 behavior from mocks or documentation.
Prepared eight-file bounded private-network in-memory OpenBao experiment using
the installed binary. No production mutations this turn. Scope, sources, risks,
root crash-cleanup limitation and exact approval fingerprint are in
[the experiment gate](evidence/D3-scoped-bootstrap-and-isolated-vault-gate-2026-10-08.md).

## 2026-10-08 — Approved fictional runtime rehearsal completed

Exact reviewed bundle staged and verified on 104, 117 and Authentik's existing
container on 106. Eight fictional protocol/revocation tests passed per target;
Authentik read-only preflight checked 21 apps and unused worker names. Removed all
enumerated staging files, independently verified absence, and checked healthy
AI-PAM readiness. No real credential/account/configuration change, restart or
model call. Approval consumed; administrative-handoff integration remains local
preparation. See [results](evidence/D3-provisioning-rehearsal-gate-2026-10-08.md).

## 2026-10-08 — Provisioning interruption handling and runtime rehearsal

Fixed unbounded partial-line reads and output waits in candidate source-local
protocol; enforced exact vault stage sequence. Added fictional revocation and
transport failure tests; 193 tests pass in restored isolated environment. Prepared
hashed source-only runtime rehearsal for 104/117/Authentik, with read-only identity
preflight and no credential use. Remote paths absent, runtime versions recorded.
No remote writes this turn. See
[rehearsal approval gate](evidence/D3-provisioning-rehearsal-gate-2026-10-08.md).

## 2026-10-08 — Vault maintenance validated and closed

Private human unseal complete; live 2.6.4 and broker TLS/identity/service readiness
verified. Removed only approved package staging; retained fresh recovery assets.
Local Doctor correction accepts only the documented retired fixture with zero
active fixture requests; nine tests pass including negative cases, and live
read-only validation is healthy. Correction not remotely deployed. No new target
action or delegation credential issued. Resume protected provisioning integration.

## 2026-10-08 — Approved vault patch installed; human unseal pending

Recovered correct human workflow from setup records: encrypted shares are in
`~/Documents/OpenBao Recovery`, separate from GPG private-key export backups.
Only filenames were inspected. Jason privately unsealed and approved continuation.
Fresh cold-service snapshot/archive passed integrity checks, then verified 2.6.4
was installed; configuration/TLS unchanged, expected sealed state after restart.
The catalogue warning matches documented retired September 27 test metadata,
not an unexplained active permission expansion. Final unseal/health/checker
reconciliation and staging cleanup remain. See
[maintenance evidence](evidence/D3-vault-maintenance-2026-10-08.md).

## 2026-10-06 — Approved vault update paused at sealed baseline

Jason approved the exact patch. Read-only preflight found OpenBao already sealed
before any maintenance; threshold 2 of 3, progress zero. Container/service started
October 5 at 16:29 UTC, consistent with but not proof of the cause. Aster/broker/
approval units remain active, which does not verify vault-dependent functions.
No production mutation. Human private unseal is required to establish baseline
before exercising the recorded patch approval. See
[preflight evidence](evidence/D3-controller-and-vault-patch-gate-2026-10-06.md).

## 2026-10-06 — Controller assembled; vault expiry advisory found

Added owned-pipe controller/node and private durable stage journal; 184 fixture
tests pass, including lost acknowledgements and refusal to replay an existing run.
During primary-source recovery research found October 1 OpenBao AppRole expiry
advisory affecting installed 2.6.3. Maintainer severity low; no exploit/compromise
inferred. Downloaded 2.6.4 locally, verified official key fingerprint, package and
checksum signatures/hash, and inspected package scripts. Read-only backup/service
baseline retained. Prepared bounded patch gate with fresh recovery checkpoint and
human unseal; no production changes or credentials. See
[evidence, sources and approval gate](evidence/D3-controller-and-vault-patch-gate-2026-10-06.md).

## 2026-10-06 — Approved Mac Keychain check passed

Exact fingerprint ran once: create, fixed reader equality, delete and helper
cleanup passed. Independent name-only query returned Keychain status 44/not found.
No real credentials, recovery material, model call or persistent item. Same-user
custody limits and legacy API warnings remain. Approval consumed; continue the
protected controller rather than repeating custody checks. See
[result](evidence/D3-keychain-custody-result-2026-10-06.md).

## 2026-10-06 — Exact Mac custody validation prepared

Added a default-inert create/read/delete check for only the fictional worker
Keychain item. It refuses pre-existing/ambiguous items and cannot delete a
mismatched value. 178 delegation tests pass; no Keychain operation ran. This
credential-store boundary awaits approval before controller completion relies
on it. Also read installed OpenBao CLI help and searched only guide filenames in
the documented human recovery bundle; no recovery material opened. See
[scope, fingerprint and cleanup gate](evidence/D3-keychain-custody-gate-2026-10-06.md).

## 2026-10-06 — Identity access guard and Mac installer prepared

Inspected installed Authentik grant/policy code and live metadata: 20 relevant
applications each bind one existing user. The candidate's conservative preflight
passed against installed ORM without mutations. Added inactive identity
provisioning and a default-inert Swift Keychain installer; 174 local tests pass.
Swift compiled with legacy Keychain deprecation warnings; actual ACL remains
unvalidated. No credentials accessed or issued. Recorded missing runnable human
ceremony instructions and same-user custody limitation before future tool access.
See [evidence and remaining controller work](evidence/D3-identity-provisioning-2026-10-06.md).

## 2026-10-06 — Approved encrypted custody host check passed

The exact approved bundle passed real encryption/decryption and transient
Aster-UID credential delivery on LXC 104. Ordinary Aster access to the stored
encrypted source was denied. The new host key is UID 0/mode 0400; only metadata
was read. Fixture, transient unit and staged tools independently verified absent.
Aster and approval services remained active; Companion HTTP 200. No real secret,
vault operation, restart, model call or push. Approval consumed. See
[host evidence and resume](evidence/D3-encrypted-custody-result-2026-10-06.md).

## 2026-10-06 — Recovery availability confirmed; encrypted custody gate prepared

Jason confirmed both required recovery keys are available, without disclosing
material. Added exact vault setup and encrypted delivery candidates; 171 tests pass.
Read-only checks verified systemd 257, Aster UID placement, OpenBao 2.6.3 and no
existing host encryption key. Prepared one fictional source-local delivery check;
host-key creation is explicit and awaits remote-change approval. No credentials,
real encryption operation, vault write or deployment occurred. See
[gate, recovery details and primary sources](evidence/D3-encrypted-custody-gate-2026-10-06.md).

## 2026-10-06 — Custody adapters and manual connected worker prepared

Added fixed-purpose vault and Keychain/Auth­entik adapters, exact proposed vault
policy/role inputs and an inert-by-default one-assignment HTTPS worker. No secret
access occurred. 163 delegation tests pass. Read official Authentik/OpenBao docs;
recorded provider-secret authority and same-user Keychain limitations. Provisioning
helper, runtime credential delivery and ACL/provider binding remain blockers.
Asked only whether human recovery material is available, not for its contents.
See [custody/worker checkpoint and sources](evidence/D3-custody-and-worker-preparation-2026-10-06.md).

## 2026-10-06 — Gateway assembly prepared locally

Composed private gateway lifecycle, owner/worker routes and deployed broker status
protocol; disabled startup creates no routes/state. Moved synchronous gate and
custody callbacks off the event loop, preserving fail-closed checks. 152 delegation
tests pass, including real local socket outage/disable checks with fixture issuer.
OpenBao service is active; current administrative bootstrap authority remains
unverified beyond the documented human recovery procedure. No credential access,
production mount, model call or push. See [assembly checkpoint](evidence/D3-gateway-assembly-2026-10-06.md).

## 2026-10-06 — Approved broker status read deployed

Updated the approved single source on LXC 104 with a root-only recovery checkpoint.
Aster's status read passed; wrong peer and actor-less management requests were
denied. Global switch and socket permissions stayed unchanged. Separate checks
found Aster/approval services active and Companion HTTP 200. No complete human
approval-flow validation is claimed. Delegation remains disabled; credential
custody and gateway wiring remain. No model call or push. See
[deployment evidence](evidence/D3-broker-deployment-result-2026-10-06.md).

## 2026-10-06 — Native Companion candidate and narrow broker status gate

Live metadata confirmed Aster belongs only to the broker approvers group, not
the general client group. Added a peer-bound one-boolean status read without
widening groups or inventing a human actor, plus a fail-closed local callback.
Added owner-only job listing and build-disabled native Companion status/answer/
stop view. 147 delegation tests, 84 broker tests (including 12 approval-service tests), 26 native Swift tests
and five JS renderer scenarios pass. Prepared exact one-file broker deployment,
baseline hash, checkpoint and rollback; no deployment, credential issue or model
call occurred. See [deployment gate](evidence/D3-deployment-preparation-2026-10-06.md)
and [custody candidate](evidence/D3-credential-registry-candidate.md).

## 2026-10-06 — Approved diagnostic stop repetition passed

One approved turn reported interrupted in 0.077 seconds, no final answer and no
diagnostic exception. Fresh read-only provider inspection independently matched
one interrupted turn and the worker ledger. The first failure remains unexplained;
do not erase it or infer a reliability rate. Added a subsequent local guard against
an extra read after a terminal notification arrives inside the interrupt RPC;
144 Python tests and five renderer scenarios pass. This guard was not part of
the successful live run and is not claimed as its cause. No deployment or push.
See [evidence and deployment preparation resume](evidence/D3-stop-diagnostic-result-2026-10-06.md).

## 2026-10-06 — Live stop reporting failure retained; diagnostic retest prepared

Approved stop test ran once: worker reported unknown in 0.075 s. Fresh read-only
inspection verified one interrupted provider turn with no final answer, but did
not establish why live reporting failed or whether the interrupt RPC caused the
stop. Two explicitly local fake-provider reproductions passed without cloud
inference; root cause remains unknown. Added fixed stage/type/RPC-code diagnostics
without error text or sensitive content. 143 Python tests and five renderer
scenarios pass. A single instrumented repetition awaits new approval; no automatic
retry or production change. See [failure evidence and gate](evidence/D3-stop-result-and-diagnostic-gate-2026-10-06.md).

## 2026-10-06 — Approved assembled worker turn succeeded

One ChatGPT-backed Codex turn through the assembled worker completed in 5.311 s.
The owner route received the exact final answer and provider usage (8,080 total
tokens). Fresh read-only conversation inspection confirmed exactly one completed
turn, no tool items and identical final text. Gateway/owner identities were local
fixtures; no production deployment is claimed. Prepared a separate owner-route
stop-after-ack mode; 141 Python tests and five renderer scenarios pass. Live stop
test awaits its own exact approval. See
[result, retained evidence and stop gate](evidence/D3-assembled-result-and-stop-gate-2026-10-06.md).

## 2026-10-06 — Finite worker assembled, live model validation prepared

Joined admission, control polling, correlated app-server Session, bounded stop,
final delivery and usage in one finite runner. 140 Python tests and five renderer
scenarios pass. The complete pilot fixture returns the exact owner answer and
preserves private state; acknowledgement/control/delivery failures do not retry
inference. Prepared metadata-only manifest with existing ChatGPT sign-in,
gpt-5.6-luna/medium and disabled tools. No new model turn or production change.
Await the [exact one-turn approval](evidence/D3-assembled-worker-gate-2026-10-06.md).

## 2026-10-06 — Approved Mac HTTPS identity test passed

The exact approved network manifest executed once: four real HTTPS requests,
all nine checks true, temporary objects removed. Independent metadata inspection
confirmed cleanup and unchanged Companion provider settings. Added durable
owner stop intent, worker control polling and numeric usage delivery; 130 Python
tests and five renderer scenarios pass. No production worker/gateway deployment,
permanent credential, model call or Git push. Both identity-test approvals are
consumed; continue worker assembly and exact credential custody preparation,
not more authentication-only experiments. See
[updated result and resume](evidence/D3-authentication-result-2026-10-06.md).

## 2026-10-06 — Approved identity experiment passed; outbound client prepared

Executed the exact approved historical canary once: all nine issuance/claim/
revocation checks passed. Independent read-only inspection confirmed temporary
objects absent and Companion provider metadata unchanged. Continued local work
on outbound worker HTTP delivery; 125 Python tests and five renderer scenarios
pass. Prepared a separately gated finite Mac HTTPS identity canary, with no
model call or production Aster deployment. See
[result, cleanup and exact next approval](evidence/D3-authentication-result-2026-10-06.md).

## 2026-10-06 — Authentication boundary and concrete identity gate

Read-only inspection verified Authentik 2026.8.0 and absence of candidate worker
identity. Installed source confirms introspection checks expiry/revocation.
Added default-disabled online worker verifier, digest-bound answer endpoint and
owner renderer projection. 117 Python tests and five renderer scenarios pass.
Prepared a temporary source-local identity canary; its metadata-only default
passed on the installed server without creating objects. Actual issuance and
revocation await explicit remote-change authorization. See
[exact scope, source hash, cleanup and acceptance](evidence/D3-authentication-gate-2026-10-06.md).

## 2026-10-06 — Local vertical handoff and owner answer delivery

Connected worker admission, private runtime, Session and snapshot recovery in a
default-disabled integration seam. Added digest-bound ephemeral answer delivery
and owner retrieval. Connection loss/restarts do not repeat inference; missing
turn acknowledgement remains uncertain. 110 Python tests and five renderer
scenarios pass. Provider exchange is simulated, not a live network integration.
Existing AI-PAM Unix peer identity and Companion public user client do not
establish a Mac workload identity. No credentials, deployment or new cloud turn.
See [result, identity boundary and resume](evidence/D3-vertical-fixture-2026-10-06.md).

## 2026-10-06 — Durable gateway/worker handoff and receipt recovery

Implemented bounded immutable job envelopes, gateway delivery and worker
admission ledgers, duplicate suppression and terminal receipt reconciliation.
Completion lost across a worker restart was recovered from the owner-bound
dispatch record and fixture thread snapshot without new execution. Added
default-disabled unregistered worker routes with dedicated identity dependency.
102 Python tests and five renderer scenarios pass. At-most-one admission is not
exactly-once distributed execution; uncertain crashes deliberately need review.
No real identity, transport or deployment is claimed. See
[handoff evidence and next integration gate](evidence/D3-handoff-2026-10-06.md).

## 2026-10-06 — Gateway reconciliation and private worker lifecycle

Read-only LAN checks found the LXC 104 gateway active with one worker and its
main source hash identical to this worktree. Mac HTTPS access to Companion
returned 200; authenticated worker access remains untested. Proposed an outbound
Mac worker through the existing private gateway, keeping Codex credentials local.
Implemented exclusive private state ownership, crash/startup uncertainty,
bounded job admission and telemetry expiry. 80 Python tests and five renderer
scenarios pass. No live mutation or new inference. See
[placement/lifecycle evidence](evidence/D3-placement-lifecycle-2026-10-06.md).

## 2026-10-06 — Usage and owner-scoped Companion candidate

Added numeric usage snapshots, owner-bound claims, uncertainty persistence,
disabled status/stop-request facade, unregistered HTTP router and text-only
renderer. 71 Python tests plus five Node scenarios pass. Existing Companion's
failed-on-restart/resend behavior is unsuitable for uncertain Codex work and was
left unchanged. Tested gateway dependencies in disposable Python 3.11 using
repository pins; system Python 3.9 could not resolve the pinned FastAPI version.
No new inference, live authentication test, deployment or push. See
[D3 evidence and resume](evidence/D3-companion-candidate-2026-10-06.md).

## 2026-10-06 — Approved subscription pilot succeeded

Jason approved the exact fictional Orion request. One ChatGPT-authenticated
gpt-5.6-luna/medium turn completed in 5.509 seconds with a usable final answer.
It distinguished known/unknown evidence without claiming inspection or repair.
A fresh restricted app-server thread/read recovered the identical answer, with
one turn and only user/agent message items. No new inference for recovery, tool
activity recorded, API fallback, production change or push. Token usage remains
UNKNOWN and live cancellation untested. See the
[result and resume point](evidence/D2-subscription-result-2026-10-06.md).

## 2026-10-06 — D2 runner prepared after offline tool-offer capture

50 offline tests pass: bounded pipe transport and restart snapshot recovery added.
The outgoing request to a local fake provider offered zero tools and carried no
Authorization header; it intentionally returned HTTP 400. No real inference.
Added a manifest-pinned single-turn pilot; metadata preparation verified native
provider, ChatGPT auth and configured gpt-5.6-luna with medium reasoning. Initial
guards stopped on implicit provider/default endpoint representations; corrected
with explicit native provider and exact canonical URL allowlist, not relaxed
custom endpoint acceptance. Actual cloud execution awaits
[the concrete gate](evidence/D2-pilot-ready-2026-10-06.md). Model choice here is a
connectivity fixture, not a sysadmin-quality recommendation. Token telemetry is
explicitly outstanding. No production changes or Git push.

## 2026-10-06 — Offline coordination and effective configuration checks

Continued Stream A locally. Added durable session coordination, early-event
buffering, typed quota/auth failures and metadata-only isolation inspection;
31 tests pass. Verified the restrictive child profile initially retained one
MCP connection; explicit inline-TOML per-server disabling reduced that to zero.
The failed quoted dotted-key attempt and successful correction are retained in
[the checkpoint](evidence/D1-session-isolation-2026-10-06.md). No inference,
credentials, saved user configuration changes or production actions. Configuration
acceptance is not yet runtime tool/context isolation; D1 remains open.

## 2026-10-06 — Subscription delegation adopted and metadata path verified

Jason directed recording the reasoning, retooling the existing project and
continuing Stream A. Adopted Codex delegation instead of further local general
sysadmin qualification; retained local functions and all evaluation evidence.
Official OpenAI auth/app-server/plan-usage and Hermes provider documentation
support the distinctions recorded in [the amendment](Codex-Delegation.md).

Installed Codex CLI 0.158.0-alpha.2.1 generated protocol schemas locally.
The initial restricted metadata probe disconnected; with platform-approved normal
runtime access, initialize/account/read/model/list succeeded: ChatGPT auth and
six catalogue entries. No thread/turn, inference, login/credential copy or
production deployment occurred. Catalogue presence does not prove entitlement.
The probe uses an allowlist of three metadata methods and suppresses account
identifiers and subprocess stderr. Eighteen offline routing/lifecycle/storage
tests pass. Durable dispatch claims survive reopening and reject duplicate claims;
this is not yet an integrated transport. Nullable message phases require explicit
abstention. The installed feature list confirms a default child may inherit tools;
tool isolation must be verified before inference. Candidate remains outside live
Aster; connected round trip and UI are not claimed complete. See
[checkpoint, schema hashes and D2 preregistration](evidence/D0-D1-delegation-2026-10-06.md).

## 2026-10-06 — Fresh paired evaluation completed and blind grades reconciled

Forty investigations / 120 calls completed with four clean contention pauses,
no recorded timeout, and healthy idle final service. Sealed scoring hash verified
before unmasking modes. Diagnostic meaning passed 20/20 in each mode; complete
correctness passed 6/20 off and 4/20 compact. Verification omissions/inadequacies
dominated failures. Off had two unsupported intermediate claims; compact had one
terminal-contract failure. Both handled all four deliberate insufficiencies;
neither claimed completed repairs or unauthorized effects.

Neither candidate passes the unchanged promotion gate. The
[decision record](evidence/SA3-fresh-evaluation-result-2026-10-06.md) recommends
an offline structured-verification candidate, not autonomous sysadmin promotion,
new hardware or another budget-tuning loop. Compact reasoning cost roughly twice
the elapsed time without better overall pass rate in this small synthetic set.
The scorer received the exact existing system verification instruction after
noticing it was absent from the masked export; no rubric change occurred.

## 2026-10-05 — Fresh paired run approved; shared model unavailable

Jason approved execution. Source and live artifact/settings checks matched.
The launch-only authentication lookup was corrected before any evaluation call;
frozen test code did not change. Repeated busy checks and a final 60-check bounded
wait found no idle slot. Final health was ok, PID 489, processing 1/deferred 0,
with no evaluation guest directory or runner. A connected client maps in the
repository to the news aggregator; request contents were not inspected.
See the [attempt and resumption record](evidence/SA3-fresh-evaluation-attempt-2026-10-05.md).
All 40 investigations remain unrun; the existing approval survives this
availability block. No scheduler, production change, model quality conclusion
or remote Git write was introduced.

## 2026-10-05 — Fresh cases sealed; paired-run approval pending

Jason approved authoring/review, carried out by separate supporting roles in
this window. Twenty fictional cases were revised and accepted before any model
run. The evaluator has not read keys. Content-free receipts, source pins,
release manifest and full runtime artifact identity are retained in Git;
private cases/keys remain outside it. This is procedural separation, not an
external human audit. Time Machine exclusion is not established.

The durable runner passes all 61 evaluation tests; the sealed package passes
offline validation. Eighty possible prompt paths fit within 1991 bytes of
message text (not measured template tokens). Current runtime PID differs from
the earlier trials; cause is unknown, with observed build/settings unchanged.
The [readiness record](evidence/SA3-fresh-evaluation-readiness-2026-10-05.md)
defines the exact next approval: 40 investigations, maximum 120 calls and
200 minutes inference on the shared local model, no real tools or repairs.
No fresh model call, deployment, source tuning or push occurred in preparation.

## 2026-10-05 — Publication verified; fresh evaluation plan prepared

Jason-approved push put `edb7cca` on Forgejo main; direct read-only GitHub ref
verification confirmed the mirror. Prepared the bounded 20-fictional-case
[one-window custody/review plan](evidence/SA3-fresh-evaluation-preparation-2026-10-05.md),
without authoring cases or running models. Tightened manifest top-level/type rejection;
all 52 evaluation tests pass. Preparation is local; corpus approval remains next.

## 2026-10-05 — Local publication reconciliation

Merged fetched Forgejo main `ec6ebd2` locally, preserving both histories and newer
unrelated projects. Retained twelve previously reviewed development records without
inventing their missing newer contract fields; evaluation readiness stays blocked
until those fields receive review. All 50 evaluation tests pass after conflict
resolution. [Publication checkpoint](evidence/SA3-publication-reconciliation-2026-10-05.md).
No push or deployment occurred; source-pin equivalence is not silently assumed.

## 2026-10-05 — Compact trial completed; budget tuning closed

Approved compact batch completed nine requests. Unavailable-evidence off/compact:
56.649/214.254 seconds; configuration-fault compact: 213.856 seconds. Both modes
showed useful evidence use, but contract/attribution/verification weaknesses remain.
Service healthy and idle, same PID, temporary guest files removed. No promotion.
[Finite-trial decision](evidence/SA3-local-qwen-development-decision-2026-10-05.md)
preserves exact outputs and closes further budget tuning. Forgejo main was observed
at `ec6ebd29c572f61aade8a91c1bff863645fd3acc`; reconcile its history before publication.

## 2026-10-05 — Original investigation batch stopped; compact candidate prepared

Approved frozen batch attempted five calls: non-thinking concluded in 56.902 seconds;
thinking hit the 300-second investigation limit during its second call. The remaining
case was not run. First postcheck saw outstanding inference; subsequent read-only
check confirmed healthy idle and unchanged PID. Preserved synthetic results and
[reviewed rubric weaknesses](evidence/SA3-investigation-development-review-2026-10-05.md).
Prepared a 384-token thinking candidate, explicit bounded follow-up schedule and
attempt/failure metadata; all 29 SA3 tests pass. No connected rerun or promotion.

## 2026-10-05 — Multi-step synthetic investigator ready

Implemented bounded simulated evidence lookup, two exposed development scenarios,
network-free default runner and containment/transport tests. All 27 SA3 tests pass;
no connected call made. [Exact proposed batch and rubric](evidence/SA3-simulated-investigation-plan-2026-10-05.md)
are ready for approval. Jason directed continued Stream A work until required gates,
with continuation after approval; no additional approval for routine local milestones.

## 2026-10-05 — Authorized off/on smoke pair completed

Jason approved two serial synthetic requests, each with a four-minute limit.
Both completed: off 24.431 seconds; on 158.706 seconds with a nonempty separate
reasoning field whose content was discarded. Same server PID, healthy afterward,
no tools, production changes, private data or retries. Both requested fresh
evidence; no quality superiority or sysadmin qualification established.
[Result and limitations](evidence/SA3-thinking-smoke-result-2026-10-05.md).

## 2026-10-05 — Per-task thinking and paired request construction

Verified the live server build and matched primary source. Both enable_thinking
and reasoning_budget_tokens can override defaults per request; loaded-template
behavior remains untested. Built offline paired request construction with tests.
[Evidence and operating profiles](evidence/SA3-per-request-thinking-2026-10-05.md)
separate thinking from authority and background scheduling. Single-slot contention
means queue priority alone cannot guarantee fast interactive inference. No model
request, service change, private data access or production promotion occurred.

## 2026-10-05 — Thinking-mode comparison and offline grading candidate

Jason requested that a fair sysadmin assessment consider reasoning enabled.
Read-only live inspection confirmed reasoning off and budget zero; installed help
supports on/off and positive budgets. Built a separate strict offline scorer and
synthetic tests without changing historical results or production. The
[paired comparison plan](evidence/SA3-fair-thinking-comparison-2026-10-05.md)
separates diagnostic quality, reasoning-mode verification, response time and later
simulated investigation. Request-level override behavior remains unverified.

## 2026-10-05 — Evaluation validity and single-window coordination

Reviewed the checked-in operational runner, scorer, preregistration and result.
Four synthetic reproductions show exact-label sensitivity, duplicate-ID acceptance
and incomplete effects rejection. No private holdout or model was accessed.
Historical results remain unchanged; no Qwen promotion or hardware verdict follows.
The [review and replacement-test proposal](evidence/SA3-evaluation-validity-review-2026-10-05.md)
defines the next offline work. Jason requested one coordinating Codex window and
plain-language updates explaining the practical implications of decisions.

## Harness follow-up

Jason asked to evaluate Hermes as a replaceable harness, compare current alternatives and recommend one implementation project document. Added `HARNESS-ALTERNATIVES.md`, linked it into the main assessment and drafted `Aster-Adaptive-Computing.md` outside the repository. Preserved the initial assessment/log/manifest under `revisions/initial-assessment/`.

Reviewed official Pydantic AI minimal loop, optional harness, slim installation, custom provider and durability documentation; LangGraph persistence; Pi core (old upstream URL redirects to earendil-works/pi); OpenAI Agents SDK; Agno; Microsoft Agent Framework; Google ADK; CrewAI Flows; smolagents; Deep Agents; OpenClaw; and Hermes. Web results are retained as `harness-research-1.json` through `harness-research-6.json`. The OpenAI documentation skill was used for its SDK portion.

Source reconciliation: a search result described an OpenAI SDK maintenance-status notice that was not present in the fetched page/official Markdown. That status claim was excluded. The web tool could not ingest the Markdown content type, so the official Markdown was fetched read-only through Python urllib and retained as `openai-agents-sdk-source.md`. No recommendation depends on the inconsistent search snippet.

Rechecked the exact historical Hermes/DeepSeek harness measurements in Local-AI. They demonstrate historical prompt/configuration overhead, not current universal relative framework performance. No candidate was installed, no new model run, and no speed/memory benchmark claimed. Recommendation is architectural fit: retain Aster baseline, evaluate minimal Pydantic AI first, selective LangGraph for explicit resumable workflows, Pi conditional on integration value.

The proposed single project is a monitored foundation release with M0–M7 gates; later programme releases remain explicitly bounded. It does not authorize deployment or automatic promotion. Report links and artifact hashes were rechecked after the supplement.

## Initial assessment log

Read-only architectural assessment. No repository or production modifications authorized or performed. Artifacts are outside repositories.

1. Read governance, portfolio, architecture, hardware, Aster operations, Second Brain, Local AI, AI-PAM, PA and bounded action records.
2. Found local main 586457f behind cached origin/main e50b670 by 15 commits. Working tree has pre-existing changes; preserved. Latest AI-PAM evidence differs materially from checkout. Cached github/main is stale and is not evidence of remote mirror failure.
3. Snapshotted non-secret tracked documentation and relevant source from cached origin/main; source-manifest.json retains per-file hashes. These are evidence copies, not repository migration.
4. Live read-only Proxmox inspection confirmed OpenBao LXC 117 running; Aster 104, inference 110, speech 116 running; VM 105 stopped; Xeon E5-2698 v4, 80338 MiB memory, 47248 MiB available at one instant, zero swap used; B60 bound to xe. PVE 9.2.20 differs from old M0 record.
5. Local aster-knowledge-mirror sibling is absent; wiki/reference siblings exist. Octelium/Jev/Decision Plane/Learning Plane terms not found in current tracked architecture search; absence does not prove undeployed.

6. Read-only direct SSH located the Forgejo repository under `/var/lib/forgejo/data/forgejo-repositories/jason/homelab.git`. An initial guessed historical `gitea-repositories` path failed; it was not treated as absence. `git rev-parse refs/heads/main` on the actual repository returned e50b670b906f397e1e70b6d51cf07e88235ac5c5. `git ls-remote https://github.com/elliottrook/homelab.git refs/heads/main` from the guest returned the same ref. No fetch or push was performed.
7. Inspected current AI-PAM, Companion, PA, Lab Operations and ARR evidence against historical plans. Current main records AI-PAM M0–M5 completion and connected Green Forgejo read integration, with native parity/write/final gates remaining. PA M0 is complete but implementation paused. ARR fixture graduation is not a natural production-remediation demonstration.
8. Read-only service queries confirmed Aster, broker, approval and Forgejo MCP gateway active on 104; llama service active and Ollama inactive on 110; speech on 116; OpenBao 2.6.3 on 117; Prometheus/Grafana on 109. The inspected Hermes gateway was inactive and no matching loaded units returned. This was not an exhaustive user-process audit.
9. Source hashes matched for live Aster agent, Lab Operations, broker core, broker approval service and Aster approval bridge. Broker transport hash differed. Reading that non-secret source showed the relevant code matched and the meaningful file difference was the opening descriptive docstring (“synthetic-only M2” versus the updated description). A copy is retained as `live-broker_service.py`; the copy has an additional terminal blank line introduced by artifact writing, so it is not asserted to preserve the live file hash byte-for-byte.
10. Ran the existing broker synthetic suite in the disposable source copy: 36 tests passed. Added two independent synthetic boundary probes using disposable databases: a different registered caller consumed another agent's request; an approved Yellow request remained consumable after demotion to probation. Results are in `broker-probe-results.json`. No production database, real approval or execution was used. These findings establish code-path gaps, not a demonstrated remote exploit or a complete security audit.
11. Inspected approval trust flow. The broker approval service trusts the allowed Aster process's supplied actor/assurance metadata; the Aster HTTP bridge validates identity. Explicit approver entitlement and independence from the model-facing process need review before expanding users/agents. Atomic consumption/concurrency needs testing; this assessment did not establish a race exploit.
12. Reviewed current infrastructure/hardware, network, backup/restore, identity, monitoring, source authority and project status evidence. Current running guest configured limits sum to about 73 GiB; instantaneous free/available host memory is not a safe additional allocation budget. Most runtime components share one Proxmox host. No machine purchase is recommended for the first experiment.
13. Reviewed related recommendation, news, document, media, subtitle, acquisition, storage, surveillance, Mac administration and external-agent pilot plans. Inventory distinguishes implementation records from proposed work, retired/declined plans and fresh observations. Peripheral reviews focused on purpose, status, architecture, dependencies, evidence and close-out; this is not a complete code audit of every project.
14. Primary-source research compared decision engines, routers, workflow engines, authorization engines, evaluation/observability platforms, serving, registries, retrieval, calibration and feedback optimizers. Tool results are retained in `research-web-1.json` through `research-web-8.json`. The assessment links supporting primary pages next to technology claims. External performance claims were not used as lab measurements.
15. Synthesized a federation under one programme. The first recommended test is read-only multi-capability routing with a strong rules baseline; a negative learned-router result is acceptable. The Learning Plane is both an independently governed subsystem and a slower cross-cutting control loop, not a runtime dependency or authority source.

## Source and verification ledger

| Evidence | Method / reference | Confidence and limitation |
|---|---|---|
| Repository baseline | Local Git status, branch/worktree/log inspection; direct remote ref queries | Exact main commit verified; local dirty work preserved |
| Project records | `source-snapshot/docs`, portfolio and manifest | Historical claims/intent; no automatic equivalence to runtime |
| Runtime guests/hardware | Direct SSH, `pct`/Proxmox read-only resources and service/version projections | Snapshot only, no sustained performance or availability claim |
| Broker code boundary | Reviewed source + live hashes/transport read + synthetic probes | Relevant path reproduced without production effects; broader exploitability not established |
| Learning/calibration/tool options | Official repositories/docs and research papers linked in assessment | Capabilities, not measured fit for this lab; live docs can change |
| Sibling knowledge repos | Local status/commit and bounded content review | Cached remote refs may be stale; no synchronization performed |

Key live hashes recorded during inspection:

```text
aster_agent.py          8777687ce97055d2db3254aa6b30ddf37fc61e73dac2bd18008cbea3fef1a8b6
lab_operations.py       0508fd95bfb71a41c55c7590538d1ed352a0d0d48211ffafe453230aa4def5f0
broker_core.py          c8f95571ab5b7be1783fe54394047a8d5c40d9cc9121ffcbdc7ad1af99a87cb1
broker approval service a73625fa3b68fe3a5e65f8960b6c96d9fec8fbf4c9dbdc75fe4136a5625c50d8
broker_approvals.py     3e376175640d7da84ab4e47b5bbc5e06075e0ce477283df2ae979e8ed44b1b0c
live broker_service.py  a45b2ff47fce65dd6c16a204979f00a9636fde4d82b799be14b867a91bf152af
repo broker_service.py  143b1d859b683b798a2a48b1b3e4c27cafd6ddcc31accd03e941b79223827890
```

Recent architectural provenance in Git:

```text
e50b670 2026-09-25 Require native Companion AI-PAM parity
c2aeb87 2026-09-25 Close OpenBao root recovery window
9c57a40 2026-09-24 Connect read-only Forgejo MCP gateway
2a0b2b9 2026-09-24 Open broker-only OpenBao service path
7297f0c 2026-09-24 Record Forgejo read credential gate
b091330 2026-09-24 Begin read-only Forgejo MCP pilot
798fe3d 2026-09-24 Verify Forgejo MCP release provenance
26fe7e1 2026-09-24 Complete AI-PAM probation lifecycle
74334af 2026-09-24 Complete AI-PAM management milestone
26854c3 2026-09-24 Deploy AI-PAM management candidate
b3619ce 2026-09-24 Complete AI-PAM mobile approval milestone
3af16b6 2026-09-24 Fix Companion approval inbox access
```

## Research limitations and unresolved questions

- No credentials, unseal shares, private keys, raw secret stores or production approval requests were inspected.
- No production fault injection, reboot, stop/start, external API mutation or new model installation was performed.
- Current host, service and hash observations are snapshots; end-to-end restoration and household failure behavior require future bounded drills.
- Personal workload prevalence, label quality, routing calibration, downstream outcome quality and sustained service objectives are not yet measured.
- Jev commercial/privacy/retention terms and comparative local-workload performance remain unverified; documentation alone does not authorize private exports.
- Octelium or other relevant work outside the searched tracked/local repositories may exist. It is explicitly UNKNOWN.
- The source manifest is a reproducibility aid, not proof that every copied file was read line by line. Core architecture/security and relevant project sections were reviewed; no exhaustive dependency/source-code audit is claimed.
- Report artifacts were written outside project repositories. No migration, archive, commit, push or production modification was performed.


## 2026-09-25 — M1 deployment preparation follow-up

Read-only service/hash/status projections on104 and read-only Authentik ORM/source projections on106 verified provider26 owner binding, subject mode, flow stages, generic ACR and the distinct authentication-method behavior. No tokens, sessions, provider secrets or recovery material were queried. The exact observations and current limitations are in [M1 deployment plan](evidence/M1-deployment-plan.md). Official OAuth2 and WebAuthn documentation was opened, but installed-source evidence governs the claim mapping. The generic ACR cannot safely be selected as passkey assurance.

Concurrent AI-PAM M6 deployment invalidated the first transport baseline; it was caught before any mutation. Re-queried hashes and service commands, matched M6's worktree source to deployed transport and preserved it while adding caller binding. Added fake-gateway denial tests; combined broker suite57 passes, staged Stage1 subset37 passes, legacy approval compatibility passes. This task has made no production or remote Git changes. A separately owned pending M6 request and deployment approval remain gates.


## Approved Stage1 execution — 2026-09-25

Jason approved the exact two-file LXC104 change. Source and database preflight,
protected backup/restore,45 guest tests and legacy approval compatibility passed.
The installer raced Type=simple socket readiness and failed closed. Read-only
diagnosis followed by one bounded same-candidate start passed. No DB restore,
credential/grant/gateway change or target write occurred. The full ten-minute observation passed; [deployment record](evidence/M1-stage1-deployment.md) holds the
exact scope, hashes, checkpoint and limits. Stage2 and Git push remain excluded.


## Offline M2 continuation

Built a synthetic-only candidate contract layer and extracted Aster selector
adapter without importing the application.28 tests and 12 fixture comparisons
pass; local timings and full source/evaluator provenance retained. No tools,
models, network or new dependencies. Existing Stage2 bridge/service suites pass
10+10; real assurance provenance remains an external verification gate.
Read a5e8b22 alternate lifecycle tests/admin diff during AI-PAM integration;
requested invariant coverage mapping instead of deleting tests to green the suite.
AI-PAM owns that reconciliation; no overlapping source edit here.


## Isolated reconciliation with authoritative f25df18

AI-PAM published its independently authorized integration while read-only
comparison was underway. Pinned the resulting baseline; seven local commits
already contained, three unique M2 commits. No authority source replay. Preserved
remote M3/M4 work and explicitly namespaced the selector-only contract profile;
29probe +52harness +76broker +163Aster tests pass. Current manifests and complete
commit map are in evidence/M2-reconciliation. Primary dirty checkout untouched;
no push or deployment by this task.


## Published integration and next M4 gate

User authorized push7133f3f; the push returned up-to-date after concurrent
publication, and read-only Forgejo/GitHub checks verified the exact matching head.
Reused existing localaf2cc4f review candidate rather than repeating experiments.
Resolved its stale header against deployed Stage1;56+29 tests and a network-blocked
164-event replay pass, with its original manifest unchanged. Prepared exact review
packet; no authenticated review or independent checkpoint custody is claimed.
The remaining gate needs human/external evidence, not another synthetic run.


## M3 representative-label design

Inventoried four payload cases, eight tool-loop scenarios, 30 authored routing
families and 12 selector fixtures; none became human gold. Drafted bounded S0-only
pilot/held-out protocol and empty forms. Review found missing semantic privacy
inheritance and ambiguous execution/label provenance; corrected those, specified
all-test second-human review, fixed statistic definitions and explicit content
review. 17 new tests pass; 73 total harness/evidence tests. Empty validation output
contains zero cases and no authority. Primary calibration references checked;
no model/cloud execution, real collection, install, deployment or push occurred.
M4 acceptance/custody and M3 human protocol/readiness decisions remain open.


## 2026-09-25 — protocol approval and custody readiness

Recorded the narrowly conveyed human design approval against the original protocol
commit/hash. Prepared a documentation-only readiness comparison: paper pilot versus
separate human OS account versus restricted Forgejo storage. Paper minimizes runtime
complexity but cannot supply machine evaluation without a later import decision.
No custody location/account, labels, cases, collection workflow or authentication
evidence was invented. Numeric retention and future acceptance tests are proposals,
not executed controls. Review clarified incident preservation must receive an explicit
human custody/deadline decision rather than unconditional destruction within 24 hours.
M4 approval remains distinct. Publication requested by Jason; remote reconciliation
must preserve the newer AI-PAM M7 work.

Technical review rejected the initial paper-default recommendation as inconsistent
with approved durable S0 Git retention and unnecessarily obstructive to evaluation.
Revised to recommend repository-native, human-reviewed S0 train/dev forms/validator;
no collection from implementation approval. Private/secret facts remain excluded.
Separate custody applies to later hidden tests and the distinct M4 checkpoint gate.


## Implementation-only S0 tooling

Recorded scoped implementation approval from coordinating task, on published
4702ee0. Added empty local forms and stdlib fixture-only reference/state checker.
Synthetic in-memory fixtures exercise transitions and adversarial privacy/revision
failures; no pilot content or human receipt was created. 23 new / 96 total tests
pass. No network/write/staging path; all authority outputs remain false. Review
requested before commit. Operational collection/retention and M4 gates remain open.

Technical reviewer independently reran the initial 18 added / 91 total tests and
accepted the non-collecting candidate. Subsequent local additions passed 23/96.
Review permits local commit only; next gate remains collection/retention approval.


## 2026-09-25 — direct bounded pilot approval

Recorded direct approval of September 26–October 25 manual pilot, including exact
case-by-case review and durable-retention limits. A coordinating message suggested
September 25; the direct approved statement governs. Clock confirms collection
not yet open. Read-only checks: `/private/tmp` Time Machine Included; existing
per-user temporary root Excluded; Spotlight disabled. No backup configuration
changed and no cases/data directories created. Third-party capture remains unknown.
No scheduler, model call, evaluation, deployment or push.


## 2026-09-26 — batch 1 direct human acceptance

Direct “Approve” response accepted all ten displayed cases and proposed labels.
Preserved exact proposal bytes and separate per-case/hash-bound acceptance record.
This is personalized review, not human authorship or independent gold. No timing
inferred; effort gate remains unknown and next batch is paused. No router/model
evaluation or execution; fixture-only validator remains unchanged.


## 2026-09-26 — batch 1 reported effort

Jason reported five active-review minutes across ten cases. Recorded as approximate
aggregate self-report; derived average30 seconds, no measured median/per-case times.
Conditional median bound50 seconds clears effort stop rule; zero unresolved
annotations. Batch2 remains AI-proposed and requires human content/label decisions.


## 2026-09-26 — batch 2 acceptance

Direct “accept” response accepted cases11–20 and their proposed labels without
revision. Preserved exact proposal/hash and separate manual acceptance receipt.
Five train/five dev; total20 accepted families. No independent-gold or timing
claim; batch2 effort remains unknown. No evaluation, execution or push.


## 2026-09-26 — batch 2 effort and final-batch preparation

“Same” resolves to five active-review minutes for batch2. Preserved aggregate
self-report and conditional median bound, no invented per-case timings. Verified
batch3 scratch directory Time Machine Excluded and Spotlight disabled before
writing. Final ten proposals remain outside Git pending case/label approval.


## 2026-09-26 — final pilot acceptance and bounded close-out

“approve 3 minutes” accepted final10 cases/labels and reported aggregate effort.
Verified all30 per-case hashes and nine artifact hashes; 20train/10dev, 3/stratum.
Total reported review13minutes. Recorded anchoring/nonblind proposal-review limits,
no independent annotation-cost or routing-quality claim. Collection closed at cap.
No evaluation, deployment, further case creation or push.


## 2026-09-26 — offline comparison planning

Read existing stdlib rules/Nearest implementation; its default evaluate entry point
tunes on another corpus and is unsuitable here. Pinned it without invocation.
Proposed fixed0.2 similarity threshold, no tuning, three engines/two input profiles,
all10dev cases retained in denominators. Context hints and exposed labels preclude
generalization claims. Privacy/model selection remain unmeasured, not backfilled
from reference labels. Wrote plan and null implementation pins; no runner executed.


## 2026-09-26 — implementation-only descriptive evaluator

Direct approval covered local code/tests, not pilot execution. Added bounded manual
evidence adapter and descriptive metrics plus pinned-source fixture comparison.
26 focused /122 full tests pass using invented in-memory records only. No accepted
case routed or fitted. Documented cooperative-budget and missing OS-launch/output
controls; no readiness claim from sandbox-exec existence. Technical review requested.

Review accepted the26/122-test candidate. Added family-alignment checks and three
more adversarial cases;29/125 pass. Harmless sandbox-exec true probe failed with
Operation not permitted (exit71); no corpus run or workaround. Recorded environment
blocker and future frozen-root/exclusive-output/hard-timeout requirements.


## Launcher readiness design and harmless primitive probes

PATH has sandbox-exec/Python, not queried container/namespace executables. Existing
Mac/Python support parent process control; six disposable fixture probes pass after
observing/scrubbing an OS-injected environment key. Full suite131 passes. Retained
blocked nested sandbox result; no weaker substitute. Documented hard isolation,
external-root, memory containment and recovery gaps. No accepted corpus accessed.


## Existing context inventory — read-only, pending review

Inspected established PVE inventory and bounded version/tool/image metadata in
LXC100/104 via direct read-only SSH. Shared Docker100 has Python3.13.5/systemd257/
Docker29.8.1/cgroupv2; no standalone minimal Python image observed.104 carries
authority services;105 is stopped recovery guest. No verified dedicated test
context. Official tagged systemd257 manuals used after rendered docs403.
Proposed conditional100 fixture feasibility design only, no worker/unit/container
created, accepted data accessed, install, infrastructure change or push.


## LXC100 feasibility candidate correction and local supervisor

Review caught invalid nested quoting. Replaced with fixed shlex-generated argv;
syntax/roundtrip/disposable local path tests pass. Added fixed-fixture-only Mac
supervisor: combined8KiB stdout/stderr bound, deadline, kill/reap, fallback command
representation and permanent remote denial.9 focused/140 full tests pass.
No remote command executed by supervisor, no accepted corpus access, no unit
started or live gate enabled. Candidate returned for review before commit.

Environment review found clear() only proved self-erasure. Added fixed locale,
systemd pre-start unset list, initial-key allowlist and early rejection before
probe imports/operations. Local invented environment tests never print values.
Added exact cleanup-mode checks and rejection tests; current13/144 pass.
Regenerated hashes; no remote unit or full payload executed, no commit yet.


## Full fixture-only probe state machine

Committed reviewed supervisor at1e506bd. Added exact fake-transport preflight,
health/DNS/control checks, ordered execution and cleanup/final verification.
Every transition has failure-injection coverage;17 new/161 full tests pass.
Uncertain ownership never authorizes stop/delete. No remote branch, accepted
data, actual DNS packet, unit lifecycle, install or push. Returned for review.


### 2026-09-26 — bounded LXC100 collector candidate

Local evidence: 15 new/176 full tests pass. Added byte/time limits to proposed
metadata collectors and PID/invocation checks to candidate ownership receipts.
No remote execution. Unloaded-unit recovery and lifecycle integration remain
UNKNOWN/unimplemented; see LXC100-CANDIDATE-EVIDENCE.md and pinned manifest.


### 2026-09-26 — integrated fixture lifecycle and recovery

184 full tests pass. Added durable intent/ownership records and receipt-guarded
cleanup; already-unloaded unit accepted only after verified completed execution
and matching canary identity with absent cgroup. Interrupted runs never replay
mutations. Live confinement and remote termination remain UNKNOWN. Candidate and
remaining-risk statement submitted for final technical review, no live invocation.


### 2026-09-26 — timing margin and manifest-bound one-shot candidate

192 full tests pass, including 8 focused timing/adapter tests. Fake-clock delayed
observations validate a single eight-second inspection deadline against the
worker's ten-second window. Fixed direct SSH and DNS adapters are implemented and
mock-tested; public invocation is disabled. Actual LXC100 support remains UNKNOWN.
Prior integrated checkpoint: `28a9e49`; current pins in the live-candidate manifest.


### 2026-09-26 — descriptor reads and conditional approval provenance

200 full tests pass, including 8 authority/read tests using temporary records and
stub execution. Bounded same-descriptor reads reject symlinks, unsafe files and
observed changes. External approval record binds the final manifest without a
hash cycle and records conveyed conditional authorization. All technical/operator/
execution release fields remain pending; no network/LXC invocation occurred.


### 2026-09-26 — coordinated single-probe release

Last preflight review passed in the coordinating task; it confirmed the exclusive
operator window and instructed release under Jason's conditional authorization.
Pending-gate checkpoint `eb1deef` preserves the preceding state. Release record
bound to regenerated final manifest; 200 full tests pass with real-record execution
mocked. No invocation by this preparation task. Final commit/hashes handed to the
coordinating task for its final verification and one authorized attempt.


### 2026-09-26 — run 001 safe read-only preflight failure

Copied/hash-verified the untouched five-record journal. No mutation intent or
ownership receipt. Coordinating task diagnosis reports an added container and
unbounded guest-root memory.max despite host-side 4 GiB LXC maxmem. Collector
assumptions need revision; this is not evidence of isolation failure. New attempt
requires separate journal, approval and fresh absent-state preflight.


### 2026-09-26 — unapproved attempt2 candidate

206 local tests pass. Dynamic inventory retains inactive containers in an exact
state baseline; fixed host-side pct accounting replaces invalid guest-root limit
assumptions. Guest MemAvailable/PSI and unit64MiB/no-swap/process limits remain.
New journal/approval identity and prior-run read-only proof prevent automatic retry.
No live diagnosis/execution by this preparation task; fresh approval still required.


### 2026-09-26 — fresh run002 approval conveyed

Coordinating task reports Jason's explicit `approve` for exactly one corrected
run002 probe once technically reviewed. Recorded separate provenance without
releasing the pending machine gate or inventing a final reviewed hash. No code,
manifest or run journal changed; no live action occurred.


### 2026-09-26 — captured pct output regression corrected

Added the full coordinator-provided host status fixture, including vmid/name/type/
tags and six pressure fields. Strict identity/metadata validation retains unknown-
field rejection. 8 focused attempt2 and 208 full tests pass. Corrected manifest
pins verified; machine gate remains closed. No live query or invocation performed.


### 2026-09-26 — reviewed run002 release-only preparation

Independent technical review passed. Updated stale approval language, exact fresh
approval provenance and released-record tests, with prepared execution mocked.
Eight focused and208 full tests pass. Final binding occurs after all pinned edits;
no invocation, fixed-journal creation, network query, commit or push in this step.


### 2026-09-26 — run002 failed safely in preflight

The coordinating task independently verified the released hashes and performed
the single approved invocation. Unit-state, path, guest-health and host-LXC-status
operations completed and resource telemetry was retained. The terminal record is
preflight failure with no mutation and no manual recovery requirement. No create,
worker, cleanup, remote-stop or corpus event exists. A later bounded DNS diagnostic
succeeded, so the exact failure remains UNKNOWN / REQUIRES VERIFICATION. Preserved
the seven-record chain, exact reviewed manifest/approval bytes and the one changed
pinned plan artifact under `run-002/`. The approval is consumed; no retry or push.


### 2026-09-26 — bounded failure-code telemetry

Implemented local-only failure boundary and class fields after run002 showed that
a broad `preflight` stage was insufficient. Codes are lifecycle-owned; classes are
limited to timeout, permission, I/O, validation and internal. Tests inject sentinel
exception text into DNS and journal failures and prove it is not retained. Default
denied transport remains distinguishable. Full suite: 210 passing. No live query,
retry, new approval, package, corpus or infrastructure change. Next decision is
whether a third fixture run has enough expected information gain to justify risk.


### 2026-09-26 — run003 go/no-go review

Decision: prepare a distinct candidate locally, but do not execute it. A final
one-shot can add evidence because both earlier attempts stopped before mutation and
the new bounded codes distinguish the unresolved preflight interval. Reusing the
run002 artifact is rejected. A disposable clone remains preferable for later
corpus/destructive work, but no verified ready target or safe spare-allocation
budget is established. Run003 must pin both evidence sets and obtain fresh approval.
A third pre-mutation failure ends live retries pending redesign.


### 2026-09-26 — run003 candidate prepared and reviewed

Created distinct attempt3 journal/manifest/approval identities. The launcher now
verifies both prior no-mutation evidence sets, including exact run002 reviewed and
consumed approval records, before any prepared invocation. Bounded failure telemetry
is the only execution-path change; commands and resource limits are unchanged.
Twenty-one focused and 213 full tests pass. Final manifest is
`188fc6a6e6ed8dda082e71c46e232145a782ad21c1ad03f795135a933ffc0c29`.
Technical review passed; human approval and execution release remain pending. No
SSH, DNS, live journal, package, corpus, infrastructure mutation or new push.


### 2026-09-26 — run003 namespace failure and verified recovery

The one approved run003 passed preflight, created the receipt-bound canary and
failed at payload readiness. Bounded evidence records `run-readiness` / `validation`;
systemd reports `226/NAMESPACE`, MainPID0 and no cgroup/runtime probe. Manual
recovery revalidated the exact invocation and canary inode/content, reset only the
failed transient unit and removed only that canary. Final unit state is not-found,
probe paths are absent, systemd is running and Docker state matches baseline.

This is a negative feasibility result for the reviewed namespace combination in
LXC100. No accepted corpus ran. The one-shot approval is consumed and run004 is
prohibited on this shared host. Next architecture work must examine a VM or a
different isolation boundary without weakening deterministic controls.


### 2026-09-26 — LXC100 retired as S0 execution boundary

Recorded an explicit architecture decision from the run003 negative evidence.
Do not bisect namespace directives on the shared household guest or weaken the
reviewed controls to force readiness. Accepted-corpus execution remains blocked.
A dedicated disposable Linux VM is the preferred future target, but VM105 remains
reserved/rejected and no capacity or placement is assumed. VM design needs its own
read-only capacity/network/image assessment and explicit creation approval.


### 2026-09-26 — disposable VM read-only feasibility

Proxmox reports 84.24 GB total /49.42 GB available memory at one instant; 17
running guests total78.38 GB configured maxima and28.70 GB observed use. Local-lvm
has665,394,887 KiB available. Existing Debian13.6 netinst ISO SHA-256
`65273beed27b2df543b68b65630ba525cfbad8df2b12035732b2dff87d6664e7`
matches Debian's archived checksum. Proposed design is1 vCPU,1 GiB RAM,8 GiB disk,
no vNIC/GPU/credentials, offline pinned input and bounded output. This is feasibility
evidence only: no VMID reservation, image download, VM creation or corpus access.


### 2026-09-26 — disposable VM concrete build gate

Selected a dated Debian13 generic qcow2 rather than netinst or the mutable `latest`
alias; observed published SHA-512
`a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c`.
Cloud-init NoCloud supplies an offline immutable seed. QEMU Guest Agent, vNIC,
credentials and shared filesystems remain absent. A strict 4-MiB/five-minute framed
serial capture carries a 2-MiB digest-bound result; rejection never auto-retries.
Planned gates are local parser/seed proof, stopped-state creation, bootstrap canary,
invented S0 fixture, then explicit boundary GO/NO-GO. No download, VM mutation,
accepted-corpus access or package installation occurred.


### 2026-09-26 — V0 bootstrap and serial candidate

Implemented a pure strict serial frame encoder/parser and deterministic offline
bootstrap-canary source renderer. Twenty focused and 234 full adaptive tests pass,
covering framing, bounds,
identity/digest checks, malformed/noncanonical JSON, candidate determinism, no
corpus/authority, no login/package/network config, systemd outer limits and
rejection of any guest interface beyond loopback. Ruby
parsed the generated cloud-config; persisted file hashes match the candidate
manifest. Candidate manifest SHA-256 is
`0d015cc70e6df5b31048fd203916dcaf0b783e8ecd3bbaae6b6c76f339610c47`.
No ISO, image download, VMID reservation, Proxmox mutation or corpus execution.


### 2026-09-26 — disposable VM V1/V2 negative result

Forgejo and GitHub mirror advanced to `dcc3623`. The dated Debian image matched its
published SHA-512 and stopped VM118 matched the reviewed one-core/1-GiB/8-GiB
networkless configuration. One approved bootstrap boot reported only loopback.
Cloud-init invoked `aster-s0-canary.service`, which failed before emitting a framed
result; the shutdown fallback powered off cleanly. Capture is 105,115 bytes, SHA-256
`23e071c370e952d64c08b678900121ee03098ec7444b1d26f5e5661fc9027fdb`, with zero
protocol records; strict parse result is `incomplete protocol`. VM118 remains
stopped, host/existing guests are healthy and unchanged, and no corpus ran. Exact
unit cause is UNKNOWN pending separately approved read-only offline forensics. No
retry or V3 is authorized.


### 2026-09-26 — V2 forensic cause and v1 correction candidate

An approved offline inspection attached VM118's stopped OS disk through a read-only
loop and mounted ext4 `ro,noload` (`norecovery`). The filesystem was clean, the
reviewed unit/canary/manifest hashes matched, and no result file existed. Seven
bounded journal records prove systemd failed before Python with
`status=209/STDOUT`: direct `/dev/ttyS0` output conflicted with
`PrivateDevices=yes`. Mount and loop cleanup were verified and VM118 remains
stopped. The v1 candidate retains private devices, writes the framed output to a
bounded file and delegates serial publication to the outer cloud-init lifecycle.
Twenty-one focused and 235 full adaptive tests pass. No new ISO or VM exists, no
boot or corpus run occurred, and V2b/V3 remain unauthorized.


### 2026-09-26 — V1b/V2b read-only preflight and frozen release

Proxmox preflight observed 48,981,213,184 bytes available memory, 664,145,554 KiB
available on active `local-lvm`, 68,233,444 KiB on active `local`, VMID119 free,
VM118 stopped and all service containers at baseline. The dated image SHA-512 and
checksum-file digest revalidated; v1 seed/ISO/release/run paths are absent. A
manifest-bound release now proposes stopped VM119 and one bounded no-retry V2b
boot, with fail-closed configuration validation and stop-and-retain recovery.
Twenty-five focused and 239 full adaptive tests pass. No remote file, ISO, VM or
boot was created; V1b/V2b await explicit execution approval.


### 2026-09-26 — V1b/V2b bootstrap gate passed

Jason approved the frozen V1b/V2b envelope. VM119 was created from a fresh import
and passed the stopped no-vNIC/no-agent validator. Its 376,832-byte seed ISO is
SHA-256 `af8278b6fe270f3a45651a376c426284d51a894fff1820173615f04051cd2ee5`.
One boot produced a 104,501-byte capture with one complete protocol envelope; the
strict parser accepted the expected run/manifest, 119 canonical bytes, result digest
and `interfaces=["lo"]`. The canary unit succeeded, no host stop or retry was
needed, VM119 is stopped, existing guests remain at baseline and no corpus ran.
V3 invented-fixture preparation is next; execution remains separately gated.


### 2026-09-26 — V3 invented-fixture release prepared

Implemented a deterministic local V3 renderer, ten-check semantic validator,
strict stopped-VM120 configuration gate, fresh-image creation script and one-boot
capture script. The fixture tests environment hygiene, unprivileged identity,
loopback-only topology, network-socket and fork denial, an inaccessible planted
canary, and read-only system paths. The reviewed unit requests private network,
syscall, filesystem and resource controls; the experiment exists to verify that
those requests are actually enforced rather than treating the unit text as proof.

Read-only Proxmox observations found `nextid=120` and retained VMs118/119 stopped.
Fifteen focused and254 full adaptive tests pass; shell syntax, cloud-config YAML and
release-manifest hashes validate. Release-manifest SHA-256 is
`f4d5b29491dafcd8393c290500da964084d5596de9943fae49b625ca854b0b6e`.
No remote staging, ISO, VM120, boot, corpus access, cleanup or push occurred. The
exact V3 window remains separately approval-gated and fail-closed.


### 2026-09-26 — V3 isolation fixture failed safely

Jason approved the frozen V3 scope. Remote staging hashes matched release manifest
`f4d5b29491dafcd8393c290500da964084d5596de9943fae49b625ca854b0b6e`.
The ISO is 380,928 bytes with SHA-256
`51cd876edbfaaaa0c6d328aced51e4aaaa47995030c5e3e39807adf11b576d2a`;
fresh stopped VM120 passed the exact no-vNIC/no-agent validator. One boot produced
a 105,156-byte capture, SHA-256
`11984e6a9cd19351a8d360c20f556d11db3c19c171879780b50c746e9e2ced86`.

Cloud-init reached `aster-s0-isolation.service`, which failed before emitting any
framed record. Strict parse result is `incomplete protocol`; no proposed isolation
check is credited. The guest powered off without host intervention, no retry or
corpus access occurred, and VMs118/119/120 remain stopped. A concurrent Proxmox
backup completed OK and explains transient container backup-lock changes. V4 is
NO-GO for accepted-corpus execution. Precise cause is UNKNOWN pending separately
approved read-only stopped-disk forensics.


### 2026-09-26 — V3 stopped-disk cause established

Jason approved the exact offline forensic scope. The reviewed script hash matched,
created a read-only loop, mounted ext4 `ro,noload,nosuid,nodev,noexec`, collected the
allowlist, then unmounted and detached successfully. The filesystem was clean and
the unit, probe and payload hashes matched the repository. `result.json` and
`protocol.txt` were absent.

Seven journal records prove systemd failed before Python with status
`226/NAMESPACE`: `/var/tmp/aster-s0-isolation-fixture-001` was not present while
setting up mount namespacing. The high-confidence design inference is that
`PrivateTmp=yes` replaced the service's `/var/tmp` view before `InaccessiblePaths=`
could mask the host-planted canary. The correction should retain `PrivateTmp` and
move the denial target outside `/tmp` and `/var/tmp`. No second boot, corpus access,
cleanup or push is authorized; the V4 decision remains NO-GO.


### 2026-09-26 — V3b correction frozen locally

Prepared a new immutable candidate rather than altering or rebooting VM120. The
single boundary correction retains `PrivateTmp=yes` and moves the planted canary
from private `/var/tmp` to `/srv/aster-s0-isolation-fixture-002`. All ten probes,
syscall filters, filesystem protections and resource bounds remain. New identities
are `isolation-fixture-002`, `aster-s0-isolation-fixture-002` and proposed VM121.

Nine focused and 263 full tests pass; shell parsing, cloud-config YAML and manifest
hash verification pass. Read-only preflight found next VMID121, the target paths
absent and memory/storage above gates. Release manifest SHA-256 is
`825d6d40cde3b1388484e37581473bb2c9c0d4e6e88d905406562536782fc4e1`.
Nothing was staged and no VM121/ISO/boot exists. V3b requires a new exact execution
approval; corpus access and push remain unauthorized.


### 2026-09-26 — V3b isolation boundary passed

Jason approved the exact V3b execution window. All staged hashes matched release
manifest `825d6d40cde3b1388484e37581473bb2c9c0d4e6e88d905406562536782fc4e1`.
The generated ISO is 380,928 bytes with SHA-256
`c8ad6005bfc221f522c4832208c6a869c936e5eddb885df4eab1f60375b07aae`;
fresh stopped VM121 passed the strict no-vNIC/no-agent configuration validator.

One offline boot produced a 104,695-byte capture with SHA-256
`5fbdb31fe58d9c2020bacca9953660dc137a5a3bbdbe081b0a83f056ecd65499`.
The strict parser accepted one complete envelope for `isolation-fixture-002`, exact
payload identity, 364 canonical bytes and result digest. The semantic validator
accepted all ten required isolation checks. The guest powered off without a host
stop; zero receipt-index mismatches were found; VMs118–121 are stopped. No retry,
accepted corpus, network device, credential, cleanup or unrelated VM mutation was
in scope.

The V4 boundary decision is GO for preparation of a fresh, separately reviewed
accepted-corpus candidate. It does not authorize corpus execution or establish
router quality, repeatability, scale or production suitability. The raw serial
capture remains on Proxmox because it contains noisy boot output and generated
public SSH host-key material; its bounded digest and sanitized decoded evidence are
retained in `run-v3b-isolation/`.


### 2026-09-26 — V5 accepted-corpus candidate frozen locally

Prepared the new-identity `corpus-descriptive-001` candidate after the V4 boundary
GO. It copies and pins the nine accepted 30-family pilot artifacts without running
the adapter or routers, and includes only the reviewed standard-library adapter,
router source and bounded worker. The comparison remains descriptive: three fixed
engines, two fixed profiles, 20 train/10 development, no tuning, model, cloud,
tool, credential or promotion path.

Proposed fresh VM122 keeps the proven no-vNIC/no-agent controls and adds exact
memory, CPU, task, file, unit and outer capture bounds. Nine focused and 272 full
adaptive tests pass; Python and shell syntax, cloud-config YAML and generated file
hashes validate. Read-only Proxmox preflight found `nextid=122`, VMs118–121 stopped,
new ISO/staging/release/run paths absent, the retained image exact and capacity
above gates. Release-manifest SHA-256 is
`1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.

No corpus evaluation, remote staging, ISO/VM creation, boot, cleanup or push
occurred. One exact stage/create/offline-boot/capture/stop-and-retain window needs
new human approval; low router agreement will be retained as a valid result and
will not trigger a retry.


### 2026-09-26 — V5 accepted-corpus attempt failed safely

Jason approved frozen release manifest
`1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`.
All 23 staged files matched the candidate and release manifests. The generated
483,328-byte ISO has SHA-256
`f425e3bd7c330886d195a6d3e4d58b9a3950607c6ddb9d3103cbe58b4d0fa6fe`;
fresh stopped VM122 passed the exact configuration validator.

The one offline boot reached `aster-s0-corpus.service`, but the unit exited with an
error before publishing any framed record. The 104,662-byte serial capture has
SHA-256 `d8dc426db310dfe2855007da0edebc96170abcb293b997d76bcf65ea4c944aa8`.
Both receipt indexes verify with zero mismatches; strict parsing reports
`incomplete protocol`. The guest powered off without host intervention, VMs118–122
are stopped, and no retry occurred.

No routing metric is credited. Exact service cause and whether any accepted row was
read or partially processed are UNKNOWN pending separately approved read-only
stopped-disk forensics. The raw capture is not committed because it contains noisy
boot output and generated public SSH host-key material. A bounded forensic plan is
prepared locally; it authorizes nothing by itself.


### 2026-09-26 — V5 stopped-disk forensics established packaging cause

Jason approved the exact read-only VM122 inspection. The reviewed script mounted
the stopped disk through a read-only loop with journal replay disabled, exported
only the bounded allowlist, then unmounted and detached successfully. The
filesystem is clean; all 15 exact generated artifacts match, and `result.json` and
`protocol.txt` are absent. Corpus content was not exported.

Twelve journal records establish `ModuleNotFoundError: No module named
'validate_label_batch'` while importing `s0_descriptive.py`. Control flow proves
the entry point first read and SHA-256 verified all nine accepted corpus artifacts,
then failed before constructing JSON blobs, parsing accepted rows, adapting them,
loading or constructing an engine, or routing. The evidence classification is
therefore hash-verification-only, with zero accepted rows parsed, adapted or routed.

Systemd also reported `RuntimeMaxSec=` ineffective with `Type=oneshot`.
`TimeoutStartSec=75` and the host's 300-second capture bound remained active. Any
V5b candidate must package `validate_label_batch.py`, prove static import closure,
remove the ineffective directive, retain effective limits, use fresh identities,
and obtain a new exact approval. VM122 remains stopped; no retry, correction boot,
cleanup, promotion or push was authorized.


### 2026-09-26 — V5b packaging correction frozen locally

Prepared a fresh immutable candidate rather than altering or rebooting VM122. The
V5b bundle adds the omitted `validate_label_batch.py`, statically verifies every
imported sibling module is packaged, and proves the generated sources import under
the guest's `-I -S -B` Python flags. It removes `RuntimeMaxSec=75`, which the V5
journal proved ineffective for a oneshot unit, while retaining `LimitCPU=70`,
`TimeoutStartSec=75` and the outer 300-second capture limit.

The nine corpus artifacts and hashes, 20/10 split, engines, fixed 0.2 threshold,
profiles, result contract and all security controls are unchanged. Fresh identities
are `corpus-descriptive-002`, `aster-s0-corpus-002`,
`aster-s0-corpus-descriptive-002.iso` and proposed VM123. Nine focused tests pass
using only invented fixture rows; candidate/release hashes, cloud-config and shell
syntax validate. The available adaptive suite passes 274 tests; the existing
`test_full_aster.py` module was unavailable because this workstation runtime lacks
`httpx`, and no dependency was installed.

Read-only preflight found next ID 123, VM123 and every V5b path absent, VMs118–122
stopped, the retained image exact and capacity above gates. Release-manifest
SHA-256 is `721c377dccca4fef1a685427d85f791559f67686b8bbf533439589f88b3a5d0f`.
No accepted row was evaluated, and no staging, ISO, VM, boot, cleanup or push
occurred. V5b execution is a separate exact human gate.


### 2026-09-26 — V5b descriptive comparison completed

Jason approved the exact V5b manifest-bound VM123 window. The first archive stage
contained 30 macOS AppleDouble metadata files; exact-set validation stopped before
ISO or VM creation. Jason separately approved a script with SHA-256
`b395d369e2d1333ea7e2c3ece141872a61818348a8ef3fcb9a0ea81f2dd18c7a`.
It verified the complete unexpected set and every intended hash, deleted only the
30 metadata files and proved the exact 24-file stage.

Fresh VM123 passed stopped no-vNIC/no-agent validation. Its 491,520-byte ISO is
SHA-256 `2de12b7c2d5e10b0c36d298ac2a89d9fbb7dae304d2c6225fa561a79b8c08627`.
One offline boot produced a complete `corpus-descriptive-002` envelope. The strict
parser and result validator accepted 36,453 canonical bytes with SHA-256
`accfb55f825605451a6742e6aa5c25b0c52b40722915f2cc737f20342bec3198`.
The evaluator took 118,140,122 ns with 20.34 MiB peak RSS. The guest powered off;
no host stop or retry was required; VMs118–123 are stopped; both receipt sets have
zero hash mismatches.

Request-only complete counts on ten exposed dev families were 0/10 abstain, 4/10
keyword and 6/10 fixed nearest. Context-assisted counts were 0/10, 3/10 and 8/10.
Nearest had full coverage but still produced missing and extra capability errors.
Context yielded two nearest gains but one keyword loss. The hypotheses pass only as
descriptive finite-corpus statements. No confidence, privacy, production-locality,
cloud need or generalization claim is made.

The disposable VM took roughly 135 seconds end to end for 0.118 seconds evaluator
work. It remains an offline evidence boundary, not a serving harness. The result
retains all three engines as benchmark baselines and authorizes no router selection,
threshold tuning, policy change, permission change, cleanup or push. The S0
comparison is complete; M3 remains open for controlled harness and local-model
comparisons.


### 2026-09-26 — M3 serving-harness decision retains Aster

Read-only checks found the Aster and llama.cpp services active with zero systemd
restarts and the authenticated inference health endpoint healthy. Aster used about
44.6 MiB and llama.cpp about 9.55 GiB at the observation point. The deployed Aster
source, current worktree source and original controlled-comparison slice have three
different SHA-256 values; this prevents treating the earlier synthetic timings as a
fresh byte-for-byte benchmark of the live service.

The retained controlled evidence still answers the architecture question.
PydanticAI slim passed the preregistered overhead and conformance guardrails, but
added roughly 22 MiB peak RSS and measurable loop overhead without removing Aster's
deterministic validation or authorization boundary. Recorded Hermes configurations
remain much heavier in prompt and wall time. Existing Aster sysadmin, Home Assistant
and mirror graduations establish useful production local-model behavior, although
they are not comparative challenger runs.

The accepted ADR retains the bounded Aster Python runtime, treats Hermes as an
optional client/workflow harness, keeps PydanticAI as a probationary specialist
challenger, and defers LangGraph and Pi until a concrete requirement justifies them.
A live PydanticAI run is rejected for now because the offline evidence supplies no
benefit hypothesis worth adding provider integration, credential handling and load
to the single-slot model. The harness subdecision is complete. M3 remains open for
representative independently reviewed routing evidence; no framework, service,
permission, policy or production configuration changed.

Follow-up source archaeology resolved the apparent live-source uncertainty. The
read-only copy from LXC 104 is byte-identical to Aster source in commit `2c71d6b`
and the current local `origin/main` tracking tree. Its delta from the Stream A
worktree is ten lines of AI-PAM knowledge-source ranking and section anchoring.
The histories are 43 commits on each side beyond their merge base, so this task did
not merge them. Future live comparison must use the eventual reconciled intended
tree; this finding does not change the retain-Aster decision.


### 2026-09-26 — S1 representative holdout proposed

Repository review confirmed S0 cannot serve as M3's independent holdout. Its cases
were AI proposed, Jason saw proposed labels, and its development families are now
exposed. Resplitting or paraphrasing them would not remove suggestion anchoring or
test exposure.

The proposed S1 plan uses 50 new human-authored, no-suggestion families: five in
each of the ten required request strata, with fixed composition/constraint and
ambiguity quotas. It compares only abstain, unchanged keyword rules and fixed 0.2
nearest trained on S0 train rows. Confidence stays null. Predeclared shadow-entry
guardrails require 45/50 complete, no prohibited or invalid predictions, constraint
and ambiguity minima, no hard privacy/locality violation and CPU p95 below 25 ms.
Passing can only justify a separate read-only shadow proposal.

No case, label, helper, custody location, experiment or service was created by the
plan. S0 collection authority was capped and explicitly excluded a later study.
S1 therefore stops before collection and requires a concrete form/validator/custody
packet, then separate collection and evaluation approvals.


### 2026-09-26 — S1 pre-collection packet prepared

The packet now contains a blank form and bundle, frozen vocabulary, JSON Schema,
syntax-only validator, invented-fixture tests and a local custody design. Review
corrected the ambiguity gate from an impossible 8/10 to 4/5, defined the full
composition/non-plan subset as the denominator with an 80% rule, and removed an
unsupported privacy-routing claim because current engines do not output locality.

The initial `/private/tmp` draft proposal failed its backup exclusion check: Time
Machine reports that path included. The corrected current `$TMPDIR` parent is
excluded, outside all named repositories and absent; Spotlight is disabled. These
conditions must be rechecked at activation. An invented Git fixture survived a
disposable bundle/clone/hash restore, which does not prove HomeLab off-host backup.

Eighteen new S1 tests and 58 combined label/S0/S1 validation tests pass. Validator
core has no network, subprocess or file access and always returns collection and
evaluation authority false. The empty template is structurally incomplete. Manifest
SHA-256 is `93b9671b4a7c8e216fec00c1351499441e6e08a1aed50f765566645f3a578911`.
No draft path, human case, service, model call, evaluation or production change was
created. The packet is ready for an exact collection decision; push remains excluded.


### 2026-09-26 — S1 collection custody activated empty

Jason approved push and continuation. Forgejo and GitHub mirror refs both verified
at `a769867e5187b30e3b8ed52613119708bab29566`. The S1 packet and all artifact hashes
revalidated before the single draft directory was created.

The current per-user temporary child is mode `0700`; its 619-byte `bundle.json` is
mode `0600` and byte-identical to the approved empty template. Validation reports
zero cases/receipts, structurally not ready and no authority claims. No request,
label, timestamps or active effort were invented. Collection starts with Jason's
first request text; evaluation and another push remain excluded.


### 2026-09-28 — S1 first accepted timer batch

Jason supplied and accepted five sanitized timer/alarm requests, then completed a
human-authored label review in a local workbook. He self-reported ten active
labeling minutes and explicitly approved durable local-Git retention. The accepted
batch passed the syntax-only validator with five receipts, frozen plan/registry
hashes and no authority claims. It supplies five timer families and five
composition cases, but no adverse-constraint cases and no complete 50-family
corpus. It cannot be evaluated or used to promote a route.


### 2026-09-28 — S1 third accepted facts batch

Jason supplied and accepted five sanitized general-knowledge requests, completed
a local no-suggestion label workbook, self-reported five active labeling minutes,
and explicitly approved durable local-Git retention. He also explicitly approved
adding the validator-required `multi-capability` tag to each facts/web case. The
accepted batch passed the syntax-only validator with five receipts, frozen
plan/registry hashes and no authority claims. It supplies five facts families and
five facts/web composition cases, but no adverse-constraint cases and no complete
50-family corpus. It cannot be evaluated or used to promote a route.


### 2026-09-28 — S1 fourth accepted media batch

Jason supplied and accepted five sanitized media requests, completed a local
no-suggestion label workbook, self-reported five active labeling minutes, and
explicitly approved durable local-Git retention. He explicitly approved adding
the validator-required `multi-capability` tag to all five cases and changing the
one internal case's cloud class to `forbidden`. The accepted batch passed the
syntax-only validator with five receipts, frozen plan/registry hashes and no
authority claims. It supplies five media families and five media/home composition
cases, but no adverse-constraint cases and no complete 50-family corpus. It
cannot be evaluated or used to promote a route.


### 2026-09-28 — S1 second accepted household-control batch

Jason supplied and accepted five sanitized household-control requests, completed
a local no-suggestion label workbook, self-reported five active labeling minutes,
and explicitly approved durable local-Git retention. The batch passed the
syntax-only validator with five receipts, frozen plan/registry hashes and no
authority claims. It supplies five home families, including one home/media
composition case, but no adverse-constraint cases and no complete 50-family
corpus. It cannot be evaluated or used to promote a route.


### 2026-10-03 — S1 closed incomplete; SA3 corpus readiness started

The S1 manifest was reconciled across all nine accepted bundles without reading
or reproducing request text in the close-out record. It contains 45 accepted
families and receipts with 50 minutes of reported active labeling effort. The
human-accepted strata are uneven (web 1, mixed 4, ambiguous 3, personal 6 and
sysadmin 6), and no accepted case has an adverse-constraint tag. The frozen S1
protocol requires 50 cases, five per stratum and at least ten adverse-constraint
cases. Therefore S1 is closed as collection-feasibility evidence only. Its
accepted records, receipts and packet are preserved, while evaluation, routing
selection, training, calibration, shadow use and production promotion remain
blocked.

The successor task is local SA3 incident-corpus readiness. Repository review found
the intake manifest intentionally empty and the existing advisor slice explicitly
development-only. The empty intake contract was strengthened to require repair
scope, expected postcheck and latency protocol, matching the existing SA3
preregistration. This added no case, reviewer, model call, provider choice,
credential, network operation or production change. Unit tests cover the new
contract and hash-bound S1 close-out manifest.

### 2026-10-03 — SA3 custody boundary template

The empty SA3 intake contract did not express custody of answer labels or the
development/holdout separation. A local empty custody template now requires a
named custodian, independent holdout reviewer, approved local storage,
answer-key separation, sanitization/retention rules and digest/freeze procedure
before collection. It explicitly blocks holdout use for retrieval and
implementation tuning, contains no case content or configured storage identity,
and is unit-tested against the intake field contract. This is readiness work
only: it did not collect an incident, contact a model/provider or access any
production system.

### 2026-10-03 — SA3 local-model candidate inventory

A direct, read-only query confirmed that LXC 110's `aster-llama.service` is
active and enabled. Its running process selects Qwen3.8-27B UD-IQ4_XS through
llama.cpp with Vulkan, one parallel slot, an 8,192-token context and reasoning
disabled. The container was running with point-in-time load averages below one
and 9,154 MiB of 16,384 MiB reported used. No prompt was submitted, credential
material was read, provider was selected or service was changed. The live,
shared one-slot service is therefore only an inventory-confirmed local baseline
candidate; it is not proof of headroom, quality, calibration or suitability.
The separate inventory record defines required pre-run controls.

### 2026-10-03 — SA3 local Qwen exploratory baseline

A single, serial, tool-free local run scored 12 of 20 sealed SA3 cases as passing
with zero forbidden effects and four invalid/runtime-invalid predictions. Median
model latency was 8.621 seconds and total model time was 175.816 seconds. The
pre-registered initial usefulness gate is at least 18/20 with zero unauthorized
effects, so the result does not select Qwen, promote routing, or permit a
production change. Two earlier transport attempts were invalid because orphaned
runner processes had unrecoverable output; they were terminated and not scored.
The final PID-tracked run was retrieved, scored offline, and all temporary
prompt/output/runner files were verified removed from LXC 110 and its host.
Detailed prompts, answer keys and predictions remain private. The loaded model
lacks a newly established immutable artifact digest, further limiting this to an
exploratory baseline.

### 2026-10-03 — SA3 development schema-conformance challenger

After the local Qwen exploratory baseline produced four malformed structured
outputs on the sealed set, a single development-only challenger used llama.cpp
schema-constrained JSON on the exposed 12-case corpus. It produced valid
outcomes, all required controls, and empty effects for all 12 cases with no
invalid output; median latency was 9.065 seconds. This is format-conformance
evidence only. It does not retest the sealed holdout, establish diagnostic
quality, select a provider, or change production behavior.

### 2026-10-03 — SA3 fresh schema-confirmation preregistration

The original sealed Qwen baseline set is permanently excluded from retest after
the development-only schema configuration was introduced. A fresh 20-case,
private, single-operator confirmation protocol now fixes the candidate, runner,
request settings and format-only decision gate before any new case/key is made.
It cannot select a provider or promote production behavior.

### 2026-10-03 — SA3 fresh schema-confirmation set accepted

Jason approved the preregistered fresh confirmation scope. A new 20-case
sanitized prompt set and separately frozen answer key were created in private
local custody, with only their digests recorded in Git. They are limited to a
single-operator, within-lab format-conformance comparison and cannot select a
provider, tune an implementation, or promote production behavior.

### 2026-10-03 — SA3 fresh schema confirmation passed narrowly

The fresh private 20-case schema-confirmation run passed its preregistered
format gate: all records had valid allowed outcomes, complete required controls,
and empty effects, with no invalid output. Its answer-key semantic score was
18/20, so the result confirms only constrained format reliability. Qwen remains
unselected for operational diagnosis because the original operational baseline
still failed. A deterministic ID remap exposed a harness issue that must be
fixed on development data, not by rerunning this confirmation set.

### 2026-10-03 — SA3 operational-quality preregistration

Schema conformance is now separated from incident quality. A proposed new
20-case quality gate fixes the current local candidate and measures bounded
planning correctness, discriminating-check coverage, evidence discipline,
controls, forbidden effects and abstention. A pass could qualify only a later
reversible read-only pilot; it cannot change authority or select a general
operational provider.

### 2026-10-03 — SA3 operational-quality corpus accepted

Jason approved the fresh operational-quality corpus scope. Twenty sanitized
private incident packets and a separately frozen answer key were created in
local custody; Git records their digests only. The corpus is not yet evaluated,
and it cannot select a provider or authorize production behavior.

### 2026-10-03 — Qwen operational-quality rejection and Responses challenger

The local Qwen quality run rejected Qwen for the read-only operational pilot:
format and controls conformed, but operational outcome/check scoring did not.
A separate stateless, tool-free OpenAI Responses API challenger is proposed for
a newly created sanitized corpus; no cloud request, credential, adapter, or
provider selection has occurred.

### 2026-10-03 — Responses challenger AI-PAM onboarding candidate

A local-only onboarding candidate specifies a service-specific OpenBao path,
stateless Responses scope, outbound-only API boundary, audit restrictions and
revocation path. It is not deployed and contains no secret, token, egress rule
or operational credential.

### 2026-10-03 — Responses challenger deployment preflight

Read-only inspection confirmed active Aster broker/approval services on LXC 104
and private active OpenBao on LXC 117. No existing Responses evaluator identity,
credential path, service, or egress rule was evidenced. No secret was read. The
bounded deployment remains blocked on a user-created OpenAI project credential.

### 2026-10-03 — Local-only operational decision

Following the subscription/API billing decision and Qwen quality rejection,
Stream A adopted deterministic, broker-gated Doctor evidence collection and
human-reviewed incident packets as the immediate operational path. The repository
contains typed investigation, retention, Doctor adapter, incident gateway and
broker gateway tests, but their runtime validation is UNKNOWN here: the local
interpreter lacks Aster dependencies and the deployed LXC lacks test files.
Cloud challenger deployment is deferred.

### 2026-10-08 — Private human ceremony preparation

Prepared a hidden-input authenticated two-share helper and a separately bounded
real-engine fixture. Fixed bootstrap cleanup on initial lookup failure; 219 local
delegation tests pass. Checked installed 2.6.4 and proposed staging absence
read-only. Source/API references, exact approval scope and remaining lost-root
reconciliation limitation are recorded in
[the human ceremony gate](evidence/D3-human-ceremony-gate-2026-10-08.md).
No production credential access, remote writes, activation or push in this step.

### 2026-10-08 — Approved two-share engine test passed

Executed the subsequently approved nine-file isolated fixture once on LXC 117.
OpenBao 2.6.4 completed authenticated 2-of-3 root generation and bounded bootstrap;
subsequent API denials verified initial root, generated root, human session and
scoped token revocation. Exact-file cleanup and independent service/staging
absence checks passed. Production AI-PAM readiness passed before and after.
No production keys, credentials or configuration used; no activation or push.
Approval consumed. Source inspection confirms cancellation cannot revoke an
already issued root; private targeted crash recovery remains the next blocker.
See [result and source references](evidence/D3-human-ceremony-gate-2026-10-08.md).

### 2026-10-08 — Targeted interrupted-root recovery candidate

Prepared human-only accessor recovery with explicit target selection, no automatic
ownership inference, no mutation retry and handled-exit revocation of the fresh
recovery root. 226 local tests pass. Prepared one bounded lost-final-response /
invalid-selection / exact-target fixture, preserving unrelated administrator
access. Only read-only staging/unit preflight performed remotely. The
[concrete gate](evidence/D3-interrupted-root-recovery-gate-2026-10-08.md) records
the archive hash, cleanup scope and production attribution limitation. No new
remote mutation, real credential access, activation or push.

### 2026-10-08 — Approved interrupted-root recovery passed

Executed the exact 11-file fixture once after Jason's approval. Real OpenBao 2.6.4
committed a root before an intentionally lost response; targeted recovery removed
it, invalid selection preserved it, and unrelated administrator access survived.
Fresh recovery roots and ordinary bootstrap credentials were verified revoked.
Exact-file cleanup, independent unit/staging absence and production readiness
checks passed. Approval consumed; no production credentials, activation or push.
The planned isolated recovery tests are complete. Resume with the real
provisioning package and its separate approval/private human-input boundary,
not repetition of passed fixture primitives. See
[full result](evidence/D3-interrupted-root-recovery-gate-2026-10-08.md).

### 2026-10-08 — Real inactive provisioning package prepared

Following approval to prepare setup, froze the 14-file package and exact controller
and human-helper fingerprints. Read-only checks confirmed all staging paths and
gateway destination absent, protected gateway directory mode, and Authentik's
unused names/signing prerequisite/21 reviewed applications. Defined fresh
recovery snapshots, private local journal, human-input sequence, 24-hour credential
lifetimes, containment and no-replay rules in the
[real setup gate](evidence/D3-real-inactive-provisioning-gate-2026-10-08.md).
No real credentials read, new accounts created, remote mutations or push performed.
Explicit production-scope confirmation is the next authorization boundary.

### 2026-10-08 — Approved staging stopped at missing container parent

Created/verified approved snapshots on 104/106/117, verified fixed Keychain item
absence without reading it, and staged/hash-checked 14 files on 104/117. Authentik
staging failed because `/var/tmp` itself is absent. Read-only reconciliation found
no partial Authentik staging. The missing-parent preflight omission is retained
as a preparation error. Local private journal parent and Swift precompile ready;
production readiness still passes. No human ceremony or credential creation.
[Checkpoint and narrow correction](evidence/D3-real-inactive-provisioning-gate-2026-10-08.md)
preserve the completed work and request only the extra parent-directory creation
and remaining Authentik staging, without replaying snapshots or successful stages.

### 2026-10-08 — Staging complete; human-input boundary

Jason authorized continuation of the narrow directory correction. Created the
missing root-0755 Authentik parent and completed only its approved staging.
Independently checked all three exact 14-file inventories, modes, owners and hashes;
frozen controller/helper fingerprints match. Existing checkpoints/staging were not
replayed. AI-PAM healthy. Await private human ceremony and non-secret completion
confirmation; the remaining original controller operation is already authorized.
No actual worker identity, credential custody, activation or push yet.

### 2026-10-08 — Real inactive credential provisioning completed

After the approved empty-attempt reset and Jason's successful private bootstrap,
ran the frozen controller exactly once. All 20 stages passed, including vault and
Keychain round trips, encrypted gateway delivery and scoped admin revocation.
Independent metadata matched six identity object IDs and confirmed inactivity and
exact bindings; temporary admin file absent; ciphertext root 0600. Exact source
cleanup and independent absence checks completed on all three targets. AI-PAM
healthy. Credential values never printed; no activation/model calls/push.
[Result and expiry](evidence/D3-real-inactive-provisioning-gate-2026-10-08.md)
retain sanitized provenance and the next disabled-deployment/pilot boundary.

### 2026-10-08 — Disabled gateway attachment prepared

Live Aster main-source hash differs from this branch. Preserved it by designing
a wrapper entrypoint rather than copying stale main code. Implemented explicit
default-off attachment and drop-in; 230 local tests pass. Read-only live checks
record service configuration, 35-route digest, health/Companion 200, delegation
404 and absent proposed files/state. Prepared a 14-member archive with exact
restart/rollback limits in the
[deployment gate](evidence/D3-disabled-gateway-deployment-gate-2026-10-08.md).
No remote mutation, credential access, activation or model execution this step.

### 2026-10-08 — Approved disabled gateway deployed

Installed the frozen 14-member wrapper/package/drop-in on 104 after exact baseline
and identity preflight. Preserved the running main application. Syntax and unit
verification passed; one service restart succeeded. Same 35-route digest, health
and Companion 200, delegation routes 404, no delegation state/runtime credential,
worker inactive and AI-PAM healthy. No rollback needed, no model call or push.
Checkpoint retained; approval consumed. See
[deployment result](evidence/D3-disabled-gateway-deployment-gate-2026-10-08.md).

### 2026-10-08 — Authenticated one-turn pilot prepared, not enabled

Added operator-only one-time admission, owner result page, and private fixed-purpose
credential-path check. 237 local tests pass; Node VM checks cover signed-out denial
and literal answer rendering. Live browser storage conventions match the page.
Read-only discovery found Aster cannot read the existing public CA and cannot
create its state under the root-owned parent; the exact gate includes a public CA
copy and private Aster-owned subdirectory. Authentik source showed disabling the
user does not alone invalidate introspection, so cleanup also revokes only this
user/provider's grants. No credential values inspected.

Codex changed to 0.162.0-alpha.2; fresh metadata and local fake-provider capture
confirm ChatGPT auth and zero offered tools. No real inference this preparation.
Frozen archive, worker fingerprint, admission specification, restart limits and
rollback are in the [pilot gate](evidence/D3-authenticated-pilot-gate-2026-10-08.md).
Await its specific approval; no deployment, activation, token use or push performed.

### 2026-10-08 — Pilot startup failed; rollback verified; narrow correction prepared

Jason approved the first authenticated pilot. Exact preflight passed; installed
the approved files and restarted Aster. Runtime failed with read-only filesystem
at `gateway.lock`: preparation missed systemd `ProtectSystem=strict` and the
notifications-only write allowlist. Unit syntax tests did not establish runtime
writability. Applied approved rollback; independently verified healthy Aster,
original 35 paths, delegation 404, runtime credential absent and unchanged main
source. Worker stayed inactive, zero grants, no ledger/job/model turn. Preserve
this as deployment failure evidence, not an AI capability result.

Corrected local candidate adds only the private delegation directory to
`ReadWritePaths`; no Python changes or additional offline model tests. The
[retry gate](evidence/D3-authenticated-pilot-retry-2026-10-08.md) binds the new hash,
retained checkpoint, one restart/turn and failure rollback. Await new approval;
no push or credential renewal performed.

### 2026-10-08 — Corrected startup passed; credential check stopped; restored

Approved corrected retry passed startup and retained original paths, strict
sandbox and exactly two writable service directories. Activated only the worker;
its one credential-path check failed before admission. Immediately deactivated
the user, verified zero grants, removed the corrected drop-in and restarted into
the healthy disabled configuration. Read-only ledger count is zero; no model call.

Broker status works as Aster, Authentik public discovery works from the Mac and
fixed Keychain metadata lookup works in both environments. Inspected OAuth HTTP
metadata has an introspection but no token request. Do not infer the precise
cause from the generic exception. Prepared a hash-bound private five-second
Keychain-read-only diagnostic with two passing fixture tests; no secret output,
network, activation or service restart. Await its narrow credential-read approval.

### 2026-10-08 — Approved private diagnostic reproduced Keychain timeout

Ran the exact fixed-item helper once after approval. Result: Keychain read timeout,
5.01 seconds, no credential output/network/model calls. No live changes. This
isolates a reproduced failure to the local private read, not Authentik or Codex.
It does not identify why the read waits. Installer source pins `/usr/bin/security`
as reader; live ACL and UI/unlock state remain unverified. Asked Jason whether a
macOS prompt appeared. Keep worker/gateway disabled; no speculative timeout change,
repeated credential read or recovery ceremony. Diagnostic approval consumed.

Jason then supplied the macOS prompt for the exact worker credential requesting
the login Keychain password. The access prompt is now confirmed; underlying lock/
ACL cause and unattended operation remain unproven. Advised Deny for the stale
timed-out request. A fresh supervised read requires a new bounded authorization;
human password stays in the OS dialog, with Allow once and no ACL expansion.

After Jason dismissed the stale prompt and requested continuation, prepared an
explicit supervised 90-second diagnostic mode. Production timeout is unchanged;
no live credential read or system change. Three fixture tests pass. The next gate
binds the new source fingerprint and one private read with Allow once, without
network, activation, restart or ACL change. Await specific credential-read approval.

### 2026-10-08 — Supervised private read passed

Jason approved the exact supervised check. It reported readable valid shape in
24.69 seconds, with no password output, network call or model call. No access
policy, account state or Aster service change. This proves supervised readability
only; human interaction time is not a Keychain latency benchmark. Current worker
re-reads Keychain for each request, so do not resume a pilot by merely increasing
timeouts. Next local design: bounded supervised session bootstrap and in-memory
short-lived token, retaining online gateway authorization/revocation checks and
no automatic renewal. No live retry or additional credential read authorized.

### 2026-10-08 — Single-bootstrap session implemented and approved

Implemented explicit supervised session bootstrap, bounded in-memory token reuse,
no renewal and sanitized stage diagnostics. 242 tests pass, including gateway
denial despite reuse. Fresh metadata binds unchanged Codex binary and configured
subscription model. Jason approved the described one-session fictional pilot.
The [session gate](evidence/D3-supervised-session-pilot-2026-10-08.md) records the
fingerprint, reservation-before-bootstrap ordering, exact cleanup and rollback.
Execution pending live revalidation; no further Keychain read during preparation.

### 2026-10-08 — Supervised authenticated round trip completed

Fresh preflight/fingerprint matched. Re-enabled only the corrected drop-in with
one restart, activated the exact identity, admitted one Orion job and ran the
approved worker once. Completed state, answer digest and usage independently
confirmed in the gateway. Disabled worker immediately; no access/refresh grants
remain. Authentik's user-deactivation signal deletes grants, correcting the earlier
incomplete inference from introspection source alone. Gateway remains healthy and
owner-readable, no active worker or scheduler. Jason's display acceptance remains
pending; app browser-open request was queued only. No push or sysadmin promotion.
Full sanitized result and provider usage: [session result](evidence/D3-supervised-session-pilot-2026-10-08.md).

### 2026-10-08 — Jason confirmed returned answer visibility

Jason reported "I can see it" with the pilot result page open. Human display
acceptance for this one supervised round trip is complete. No further inference,
credential read, service change or push. This does not assess answer quality,
unattended operation or general sysadmin readiness. Next local work is normal
Companion request/result integration and remaining lifecycle acceptance, not
another repetition of the successful fixed Orion pilot.

### 2026-10-08 — Native reviewed-request candidate

Jason selected native Companion. Implemented owner-reviewed text intake, explicit
cloud consent, digest-bound one-assignment worker delivery, no automatic retry,
and metadata-only pending-request recovery. No history or tools are attached.
Codex history retention is disclosed separately from gateway memory-only text.
Read-only installed-app/gateway checks retained in the
[native gate](evidence/D3-native-request-gate-2026-10-08.md). Live systems remain
unchanged; package preparation does not register, install or launch the app.
This is a supervised workflow candidate, not a sysadmin promotion.

### 2026-10-08 — Approved native deployment installed

Jason approved. Verified baseline and artifacts, preserved gateway and app recovery
copies, installed the bounded candidate, and confirmed healthy Aster, preserved
routes and denied unauthenticated intake. Native app launched. Worker is inactive;
no new credential read or model turn. Await user readiness at review screen before
one admitted request. See native gate for exact resumable state and cleanup.

### 2026-10-08 — Native sign-in blocker repaired locally

Jason reported the native app stuck on Signing in. Source inspection found
`completion?(await exchangeCode(...))`: optional chaining skips argument evaluation
when the ordinary login caller supplies no completion closure. Thus a successful
web callback can skip token exchange and leave isSigningIn set. This is a verified
source defect consistent with the screenshot; no secret-bearing traffic was
inspected to claim a captured live callback. The prior tests covered refresh but
missed callback-free initial sign-in.

Separated unconditional exchange from optional completion notification, retaining
callback validation, generation guard, PKCE, passkey and persistence policy. Added
synthetic initial-login and failure-notification tests; all 30 native tests pass.
Built and installed 0.3.0 build 6 as the narrow repair requested by Jason.
Signature and installed-file hashes verified; pre-repair build 5 retained at
`/Applications/AsterCompanion.pre-authfix-20261008.app`. Original pre-Codex recovery
copies remain untouched. App reopened; real sign-in acceptance remains pending.
No gateway changes/restart, credential read, worker activation or inference.

[Repair manifest](evidence/D3-native-authfix-artifacts-2026-10-08.json) supersedes only the
app portion of the original artifact manifest; gateway and worker hashes remain
unchanged. Stop before request submission until user sign-in/readiness confirmed.

### 2026-10-08 — User-authored native round trip completed

Reconciled Jason's already-submitted request without resending. One queued request
was valid; assignment-only manifest differences matched. Ran one no-tools turn,
confirmed gateway completion/answer digest/usage, then disabled worker and verified
zero active grants. Owner answer visibility remains pending; preserve in-memory
answer before the already-approved intake-closing restart. No second inference
is authorized. See native gate for exact resumable state.

### 2026-10-08 — Native answer accepted and session closed

Jason confirmed native answer visibility. Closed intake with the approved narrow
drop-in removal/restart; health 200, all original 43 API paths, both completed
records preserved. Independently verified worker inactive and no access/refresh
grants. Native UI round trip accepted; D3 operational lifecycle work remains.
No more inference or push authorized by this consumed one-turn gate.

### 2026-10-08 — Closed availability and missing-answer candidate

Prepared authenticated read-only closed-intake status and honest native messages
for unknown readiness and completed-but-unavailable answers. 33 native and 252
backend tests pass; signed build 7 packaged locally. No live change or inference.
See [bounded gate](evidence/D3-availability-gate-2026-10-08.md) for deployment,
rollback and subsequent session/recovery work.

### 2026-10-08 — Availability candidate deployed and visually verified

Jason approved. Gateway checkpoint, two-module update and one restart passed;
health 200, 44 scoped routes, anonymous denial, new submission absent and two
completed records retained. Signed Companion build 7 installed with whole-app
backup; native UI visibly disables Ask Codex and honestly marks the completed
answer unavailable. Worker remains inactive. See [gate](evidence/D3-availability-gate-2026-10-08.md).

### 2026-10-08 — Session and recovery boundaries extracted from code

The accepted pilot exposed a four-minute manually coordinated submission window
and 15-minute in-memory answer window. Reviewed source for intake, gateway ledger,
worker token/session, dispatch store, Codex thread creation and recovery parser.
[Design candidate](evidence/D3-session-and-answer-recovery-design-2026-10-08.md)
separates owner, readiness, execution and answer availability; recommends an
offline lease experiment and exact-turn recovery fixtures before live authority.
No service or credential changed for this design work.

### 2026-10-08 — Offline supervised-admission contract passed

Implemented a volatile, synthetic lease prototype for one reviewed job. It
closes on heartbeat/credential expiry or restart and forbids reopening after an
uncertain or consumed session without explicit closure. Full delegation suite:
257 tests passed. No gateway transport or worker authority wired. Live admission
requires verified worker identity and atomic lease/job SQLite transaction; see
[design](evidence/D3-session-and-answer-recovery-design-2026-10-08.md).

### 2026-10-08 — Offline exact-turn recovery contract passed

Added owner/job/thread/turn/digest-bound final-answer verification around the
existing snapshot parser. Synthetic tests reject owner mismatch, incomplete or
contradictory snapshots, altered answers and duplicate turns. Full delegation
suite: 261 pass. No Codex history read or live change. Protocol compatibility
and authorized credential lifecycle remain unverified; see
[design](evidence/D3-session-and-answer-recovery-design-2026-10-08.md).

### 2026-10-08 — Fictional Orion exact-turn read verified

Official [App Server documentation](https://learn.chatgpt.com/docs/app-server)
confirms read-only `thread/read` with `includeTurns`. The installed app-server
returned the stored fictional Orion turn by its known ID, and local owner-bound
recovery verified the final-answer digest against Aster's durable record. Only
booleans were printed; no new inference or worker credential read. This is
compatibility evidence for one stored turn, not authorization or a retention
guarantee. Owner-facing recovery remains a separate gate.

### 2026-10-08 — One SQLite transaction for session admission

Moved the offline readiness prototype into the existing gateway ledger and
removed the now-redundant in-memory implementation. A single transaction claims
one fresh, owner/worker/model/plan-bound session and inserts one durable job;
capacity/duplicate failures roll back both. Unknown work prevents closing the
session and opening another. Backend suite: 264 tests passed. No live route or
identity activation. [Result and remaining gates](evidence/D3-session-and-answer-recovery-design-2026-10-08.md).

### 2026-10-08 — Owner-requested recovery ticket and offline transport

Added a one-ticket, owner-bound recovery ledger and unattached owner/worker
HTTP candidate. An exact local thread reader can return only the original final
answer after digest verification; no model turn path exists. Fixture and ASGI
client tests passed (279 backend total). Production routes remain absent and
worker inactive. See [design](evidence/D3-session-and-answer-recovery-design-2026-10-08.md).

### 2026-10-08 — Recovery integration prepared; live gate remains closed

Added a strict recovery-only gateway flag, authenticated owner/worker recovery
mount, and native Companion build 8 explicit recovery control. Request intake
remains closed; the UI advertises no worker readiness and sends no automatic
retry. Built a Mac runner limited to the original completed dispatch record,
metadata methods and exact `thread/read`; it opens the old SQLite dispatch
record read-only/immutable and prints no content. Full local suites: 282 backend
and 35 native tests pass. Signed app candidate packaged locally, uninstalled.

Read-only live check found LXC104 active and fictional Orion still completed
with its durable answer digest. Metadata-only Codex preflight passed with
ChatGPT authentication, native provider, zero enabled MCP servers and no model
call. One first preflight attempt was denied in the sandbox; a read-only
escalated metadata preflight then succeeded. No Keychain read, ticket, identity
activation, app installation, gateway change, inference or push occurred. The
[bounded gate](evidence/D3-answer-recovery-gate-2026-10-08.md) documents exact
source hashes, original-answer limits, rollback and fresh approval required.

### 2026-10-08 — Approved one-time original-answer recovery passed and closed

Jason approved, paused, then resumed the bounded fictional Orion trial. The
pause was handled by removing the temporary flag and confirming the original
44-route safe state; no ticket or worker grant existed then. On resume, exact
hashes, checkpoints, inactive identity and expiry were rechecked. Signed native
Companion build 8 was installed. Recovery-only flag mounted four routes while
request intake stayed closed. The Mac runner's metadata manifest matched its
frozen fingerprint. Jason pressed Recover once; the worker claimed exactly one
ticket, read only the stored original turn, verified the durable answer digest
and returned `completed`. The Mac dispatch database was unchanged and gateway
job count remained two. No new model-turn method existed in the runner and no
answer text entered operator output or Git.

The worker was disabled immediately; independent Authentik checks showed zero
nonrevoked grants. Jason confirmed the answer visible in native Companion and
approved closure. The exact temporary flag was removed and Aster restarted;
health and 44 routes passed, new submissions and recovery absent, two jobs and
one completed recovery ticket retained. The answer is again unavailable in
Aster after restart by design. The signed build 8 and private recovery copies
remain. [Full bounded result](evidence/D3-answer-recovery-gate-2026-10-08.md).
This is one successful recovery, not D3 graduation or authorization for a
standing service, new sysadmin tools, further inference or a Git push.

### 2026-10-08 — Session readiness review and local stop-admission correction

Reviewed the current gateway ledger, Authentik worker verifier, Mac worker,
request intake and native Companion flow after Jason confirmed the recovered
answer. The ledger can atomically admit one job, but it cannot establish Mac
worker readiness: the verifier previously discarded the verified token expiry,
the current worker starts only after a job ID exists, and intake still bypasses
session admission. Mounting the existing session methods would leave the
four-minute operator race in place. A user-started, one-question Mac session
is the next falsifiable design candidate; it requires no standing tools or
worker.

Separated stopping new admission from reconciling an admitted job in the local
SQLite candidate. An uncertain job remains visible and blocks another session
until explicitly reconciled. Older candidate schemas migrate without resetting
their ledger. The local verifier can now return the worker's expiry from its
same online-validated Authentik response while preserving current routes.
Synthetic wrong-owner, pending-job, schema-upgrade and expired-identity checks
pass; full backend suite: 286 tests. No live route, credential, worker or
production service changed. See [the post-trial review](evidence/D3-session-and-answer-recovery-design-2026-10-08.md).

### 2026-10-08 — Challenge to the distributed native Codex path

The post-trial code review found that the worker identity is deliberately
inactive between trials; the gateway broker exposes only a global automation
status, not owner/session authorization or Mac process startup. The current
worker credential expires on 2026-10-09 at 19:02 Vancouver time. A normal
Companion Start button over the gateway therefore requires a new, reviewed
activation and credential lifecycle; gateway session routes alone cannot make
it usable. No identity, broker or credential was changed.

For the signed native Mac app, a one-shot local Codex App Server bridge may
deliver the same reviewed no-tools question with fewer authorities and no
worker credential. This is a proposal, not validated implementation. A
synthetic, no-inference comparison must test startup, isolation, crash,
duplicate-click and recovery behavior against the existing distributed path.
If it passes, use local direct delegation for first normal native use and retain
the gateway adapter only for future remote/voice needs. See [the comparison and
falsification criteria](evidence/D3-session-and-answer-recovery-design-2026-10-08.md).

An offline `local_turn.py` candidate now reuses the existing durable one-turn
session and dispatch store with a fake Codex agent. It does not launch a
process, call a model or contact the gateway. A lost start acknowledgement
cannot dispatch the same job twice; the store contains no prompt or answer;
unexpected tool requests are refused and interrupted on a best-effort basis.
Synthetic completion, duplicate, tool-refusal and timeout checks pass; the full
backend suite is 292 tests. This proves only the local coordinator's failure
semantics. Signed native packaging and actual App Server isolation remain open.

The disabled-by-default `local_bridge_cli.py` candidate now wraps that local
coordinator. Default execution is inert; `--prepare` performs metadata-only
Codex account/model/configuration and hash checks, while future `--run` requires
an exact manifest and strictly consented stdin request. No prompt goes in argv,
environment or the dispatch journal. Synthetic input/default tests raised the
backend total to 295. The system Python default invocation passed. The first
metadata-only App Server preflight failed to start inside the sandbox; the same
read-only preflight passed with platform-reviewed unsandboxed execution and
reported ChatGPT auth, zero MCP servers, read-only sandbox, disabled web search,
model `gpt-5.6-luna` and fingerprint
`f5f072f6d7395d0b9b77775155239d87e913c38f2adb6acb6b0e1122c5101cd0`.
No model turn, native app launch, credential read, gateway route or production
change occurred. The installed interpreter/module packaging burden remains an
open comparison against the distributed worker.

### 2026-10-08 — Signed native local pilot prepared, still uninstalled

The Companion build script now bundles only twelve allowlisted stdlib Python
bridge modules before signing and can skip Launch Services registration for a
local candidate build. A signed build 9 was assembled and verified without
replacing installed build 8. Its helper is inert by default and completed the
same metadata-only ChatGPT/no-MCP/read-only preflight under the minimal
environment used by the native launcher. The manifest remains
`f5f072f6d7395d0b9b77775155239d87e913c38f2adb6acb6b0e1122c5101cd0`.

The native pilot screen is hidden unless the app launches with an explicit
pilot flag. It shows only the prior fictional Orion question, requires a
separate cloud-consent click, records a unique request ID before process start,
passes the reviewed frame through stdin and displays a volatile final answer.
The launcher bounds stdout, times out a hung child and refuses an invalid
manifest hash or unsafe journal path. A fake Codex executable completed one
full Python bridge round trip and duplicate refusal. Current local results:
296 Python tests and 43 Swift tests pass; signed bundle verification passes.
No real model turn, installed-app replacement, credential read, gateway route,
worker activation, production change or push occurred. The exact connected
trial and rollback are in [the native gate](evidence/D3-native-local-bridge-gate-2026-10-08.md).

### 2026-10-08 — One native local bridge question completed

Jason approved the signed build 9 replacement and one fictional Orion question.
The pinned bundle and ChatGPT/no-tools/read-only manifest matched before install;
a verified whole-build-8 rollback copy was retained. Jason reviewed the fixed
question and consented in Companion. The UI displayed one completed answer, and
the private local journal recorded exactly one completed request with one
thread/turn ID and no durable prompt or answer. Aster's gateway remained closed
at 44 paths and two historical jobs; the separate worker identity stayed
inactive with zero unrevoked grants. This supports the feasibility of a native,
subscription-backed, no-tools adapter without gateway activation for a single
question. It does not yet establish normal-use reliability, response-time
performance, remote/voice suitability or sysadmin capability. See [the bounded
trial record](evidence/D3-native-local-bridge-gate-2026-10-08.md).

Jason authorized closing the answer. The signed-in normal screen was visible
after closing the pilot sheet. Companion then quit and restarted without the
pilot flag, still from the signed, pinned build 9. Its process is running, but
the screen-control tool initially timed out reading the new window. A process
sample localized the wait to the existing macOS Keychain session read. After
Jason handled the prompt privately, the signed-in normal UI was visible, with
the pilot control hidden and normal Codex intake still closed. The journal was
preserved at one completed turn; the gateway remained at two jobs. No second
model request was made. Ordinary household actions were not exercised.

### 2026-10-09 — Native normal-use acceptance plan, no new live turn

The first native answer proves a transport path, not routine value. A finite
12-question, fictional/non-sensitive [preregistration](evidence/D3-native-normal-use-preregistration-2026-10-09.md)
now states the hypothesis, failure conditions, frozen classes, measurements,
security invariants and promotion boundary. A signed, uninstalled build 10
prototype now presents exactly the twelve fictional questions behind a separate
launch flag, with per-question consent, one-turn idempotency, owner-bound
read-only status and content-free private timing/event records. It offers no
arbitrary question entry. **297 Python and 46 native tests pass**; the bundled
metadata-only preflight still pins ChatGPT auth, zero MCP servers, read-only
sandbox and no web. Independent label review, answer scoring and connected
recovery testing remain open. The plan authorizes neither live questions nor a
new app installation. Keychain startup friction is included as observed
evidence rather than hidden as setup noise.

### 2026-10-09 — First finite-evaluation click stopped before model launch

Jason approved the exact build 10 first-case gate. The signed, pinned build
was installed with a verified build 9 rollback. The normal Aster screen and
fixed first-question review appeared after Jason handled a macOS Keychain
prompt privately. He checked consent and clicked Send once. Companion reported
“Private journal unavailable. Nothing was sent.” The local journal remained at
one historical request/turn; the evaluation log and pending ID were absent.
The question therefore did not reach Codex.

Foundation reproduction traced this to attempting to create an already
existing private directory with `withIntermediateDirectories: false`; it
throws file-exists rather than returning success. The source now accepts that
specific condition only after verifying canonical directory type, owner and
owner-only mode. Repeat-call and file-substitution regression tests and all
47 native tests pass.
The corrected signed, unregistered build 11 keeps the same no-tools/read-only
manifest. [A separate gate](evidence/D3-native-build11-first-case-gate-2026-10-09.md)
is prepared for a new install and first question; no second attempt has run.

### 2026-10-09 — Corrected first finite-evaluation case completed

Jason approved the separate build 11 gate. The signed, pinned build replaced
build 10 after preserving verified build 9 and build 10 rollbacks. One reviewed
fictional HTTP 503 question completed through the existing ChatGPT sign-in with
no Aster tools or gateway route. The answer separated temporary service
unavailability from proof of a lasting outage. One new local journal request
has one completed turn and usage record; the owner-only event file has just
submitted/completed metadata for case 0, with 2.273-second turn time and
3.044-second send-to-result time. Aster retained 44 paths, GET-only owner job
listing and two gateway jobs. The separate worker remained inactive with zero
unrevoked grants. Jason then approved closing the volatile answer. Companion
quit and reopened in normal signed-in mode; the evaluation control was hidden,
ordinary Ask Codex intake stayed disabled, the local journal/event counts did
not grow, and the gateway remained closed at two jobs. This is one successful
transport and measurement case, not routine reliability, automatic routing or sysadmin
qualification. The other eleven cases were not run.

At Jason's explicit request, the Mac's local inactivity controls were changed
for this long-running supervised work: screen saver start and display-off are
both two hours, and password is required immediately when either starts. The
Lock Screen and Screen Saver settings were verified in System Settings and
`pmset -g custom` reported `displaysleep 120` on AC. The prior visible settings
were 20 minutes for screen saver, 10 minutes for display-off and a four-hour
password delay. This is a workstation convenience/security tradeoff, not
evidence that LAN controls are sufficient; no network access setting changed.

### 2026-10-09 — Native Companion Keychain migration failed the update gate

With Jason's approval, signed version 13 migrated the saved login from the
legacy `oidc_session_v2` item to a new, app-only `oidc_session_v3` item.
Keychain Access metadata confirmed the new item existed, had one allowed
`AsterCompanion.app` entry, and did not allow all apps. Version 13 opened
signed in and restarted without a prompt. A same-signer, same-bundle-ID
version 14 update nevertheless produced another Aster Companion Keychain
password prompt for the Companion service, as Jason confirmed. This fails
the standing-access update criterion. Signing continuity and new-item
creation are insufficient on this Mac, even though both passed local tests.

The planned version-11 binary rollback opened with an expired/revoked legacy
session, so it was not a viable authentication rollback. Version 13 was
restored, opened signed in, and restarted normally. No Keychain ACL was
broadened, no password/token was inspected, and version 14 was preserved for
diagnosis. The next hypothesis must use a materially different storage or
trust mechanism, be tested first with disposable credentials, and explicitly
account for refresh-token rotation during rollback. See
[the detailed evidence](evidence/D3-native-stable-signing-keychain-design-2026-10-09.md).

### 2026-10-09 — Scope the next native login design before another live test

Read-only signing metadata for the restored version 13 shows no Team ID and no
entitlements. Apple distinguishes the file-based and data-protection macOS
Keychains; the latter uses app identifiers and validated entitlements. The
[custody decision](evidence/D3-native-session-custody-decision-2026-10-09.md)
therefore keeps version 13 as the working app and treats a disposable-item
data-protection probe as the next smallest falsifiable experiment. A new local
credential broker would add enough IPC and lifecycle complexity that it is
deferred until update-prompt frequency or availability evidence justifies it.
No live credential, production infrastructure, ACL or signing identity changed
in this decision step.

### 2026-10-09 — Disposable modern-Keychain probe rejects current signer

Built two isolated test app versions using the existing local Companion
signing identity, a separate bundle ID, and a synthetic service/account/value.
Both signatures and matching designated requirements verified. The first
data-protection Keychain add failed with `-34018` (missing entitlement) when
run outside the command sandbox; no test item was created and the second
version had nothing to read. An earlier sandboxed `-25291` result was treated
as environment-limited, not evidence about the Mac Keychain. No real saved
login was read or changed, no Keychain ACL was broadened and no prompt was
triggered. This closes the simple “set the modern Keychain flag” hypothesis
for the current self-signed app. A Developer ID path remains conditional on
owner choice and a new synthetic test; see the
[decision record](evidence/D3-native-session-custody-decision-2026-10-09.md).

### 2026-10-09 — Installed version 13 read-only session follow-up

Companion still showed the signed-in Aster screen. Keychain Access metadata
showed its `oidc_session_v3` item modified one hour after creation, without
revealing the value. The AI-PAM sheet completed a read-only refresh without a
visible error or Keychain prompt. This shows current authenticated operation,
but the modified time alone does not prove a successful refresh-token path.
A new synthetic regression test asserts refresh performs one `v3` write and
no post-save Keychain read; 14 focused native auth tests passed. Deliberate
expiry, sleep/wake and crash reconciliation remain open; no model call,
approval action or infrastructure change occurred.

### 2026-10-09 — Offline restart guard for uncertain Codex turns

Added a fake-agent test that loses the turn-start acknowledgement, closes and
reopens the private dispatch store, and then attempts the same request ID.
The reopened store retains `unknown` and refuses a second thread or turn.
Thirteen local-turn/local-bridge tests pass. This directly tests durable
duplicate prevention across a process restart; it does not substitute for a
live app crash, Mac sleep/wake, or recovery of an already completed answer.

An additional synthetic subprocess exits abruptly inside the fake agent's
`turn/start`, after the SQLite dispatch claim but before any acknowledgement.
On reopening, startup reconciliation changes the durable `dispatch_unknown`
state to `unknown` and refuses a second turn for the same request ID. Fourteen
focused tests pass. This exercises a real local process-death boundary with no
Codex process, cloud request, live credential or Companion interruption. Live
app crash/sleep/wake behavior and original-answer retrieval still need their
separate gates.

### 2026-10-09 — Disabled native manual Codex candidate

Prepared a separate manual Companion surface behind
`--aster-local-codex-manual`. It reviews arbitrary text and requires explicit
ChatGPT consent per question, then uses the existing one-turn, no-tools local
bridge. A private content-free pending record is durably claimed before helper
launch; only a completed original answer can be acknowledged to admit a new
question. Two pending-record tests and all 55 native tests pass. Built an
unregistered, uninstalled ad-hoc app and verified its strict signature.
Metadata-only preflight matched the pinned manifest and reported no inference.
No user question or model turn was sent, no app was installed, and no real
credential value was inspected. The candidate still needs signed-release and
live reliability gates before manual use.
