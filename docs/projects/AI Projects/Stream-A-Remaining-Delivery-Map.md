# Stream A — remaining delivery map

**Owner-facing checkpoint, 2026-10-09.** This page translates the detailed [programme](Aster-Adaptive-Computing.md) and [Codex delegation gates](Codex-Delegation.md) into the next decisions. It does not authorize a deployment, additional cloud question, new tool grant or Git push. Evidence links control factual claims; an unchecked gate remains open even if a nearby experiment passed.

The [October 14 evening execution decision](evidence/Evening-execution-decision-2026-10-14.md)
separates the actual backup/check schedule from the proposed live windows,
records both measured full-stop blockers, and sets the October 15 deadline
expectation. It supersedes any statement that lab time alone remains.

The [full-stop recovery dependency tracker](Full-Stop-Recovery-Dependency-Tracker.md)
is the current checklist for the exact receipt, watchdog, approval, drill and
restoration gates. It marks only observed steps complete and separates the
October 16 read-only scan from an unscheduled live drill.

**October 25 evaluation watchdog checkpoint:** the fifth source-only F6 packet
at implementation `780c33e2` and card `75b423d4` closes the earlier wrapper,
owner-liveness and live-observation defects. Independent clean-archive review
matched all thirteen card hashes and passed 51/51 focused tests; target
preflight found every destination absent and the installed disabled
evaluation-entrypoint baseline exact. The packet is ready for one separately
approved inactive installation. No watchdog/heartbeat unit is installed,
enabled or armed yet; F6 and live D4/M3 evaluation remain closed. The October
26 F2 run is independently scheduled and conditional. Jason approved the
bounded inactive installation, which now passes with 51/51 target-Linux tests,
exact installed hashes, disabled/inactive units and no runtime state. The next
F6 step is a source-only activation card and read-only healthy-lease preflight;
identity creation, timer arming and recovery remain unapproved.
The platform-owned candidate-H admission implementation at `f109c1f0` has now
passed independent source review and the exact approved inactive installation.
All four installed hashes and root custody match, the target-Linux suites
passed 69/69 plus the isolated real-wrapper test, rollback is retained, and no
lease, F4/F5 artifact, timer, process or workload was created. This closes the
inactive source-compatibility step only. Tonight's independently scheduled F2
cycle must still succeed before F3, F4 and the fresh F5/admission production
sequence can run; F6 recovery remains disabled and candidate H/M3 remain
unspent.
The first acquire-only/start split at platform commit `2f790b63` passes 36/36
clean-archive tests and closes the legacy acquire→post shortcut, but its
[independent review](evidence/Stream-A-two-phase-evaluation-adapter-review-2026-10-25.md)
found that consumer mask/stop commands run before the durable state becomes
`QUIESCING`. A crash can therefore leave partial effects recorded as the
pre-effect phase. The source is not installed; a durable-before-effect ordering
fix and partial-failure recovery regression are required.
Stream A has now produced that source correction at local commit `d2e296ee`:
the durable phase precedes the first consumer command, partial failure and
prepared-state recovery are covered, and the bound watchdog handles healthy,
owner-lost and expired prepared leases. A clean archive passes 39/39 focused
tests. The platform owner integrated it at `bdf745aa` and corrected the four-path
upgrade card at metadata commit `dfeb1374`. Jason approved the exact inactive
upgrade; the complete packet passed 39/39 clean and target-Linux tests, all
four installed hashes and root:root 0644 metadata match, a root-only rollback
checkpoint is retained, every F6 unit remains disabled/inactive and no runtime
state exists. The next bounded gate is the prepare-only healthy-lease and
recovery exercise; consumer quiescence and model calls remain closed.

The approved prepare-only exercise subsequently reached healthy durable
`PREPARED` state but [failed closed during recovery observation](evidence/Stream-A-prepare-only-exercise-live-result-2026-10-25.md).
The exact lease was cancelled safely before deadline with no consumer command,
model request, receipt or residual runtime state. Repetition isolated an
intermittent `/proc` GPU-holder enumeration race: backend, metadata auth and
idle checks passed 10/10, while GPU enumeration passed 9/10. Stream A's narrow
source-only correction at `c370cce4` ignores only a fully vanished process,
keeps all live, malformed, foreign and additional-holder cases fail-closed,
and passes 90/90 clean tests. Platform integration, target-Linux proof and an
approved inactive observer/runner replacement precede any new live attempt.
That revised replacement is now installed: an incomplete test archive first
rolled back cleanly, then the complete clean archive passed 90/90 target tests.
The installed correction passed 20/20 read-only live observer calls and full
exercise prestate with clean custody, healthy production and unchanged F2.
The next F6 gate is one newly carded and separately approved live prepare-only
exercise; no retry was inferred from the installation approval.
That [one-attempt exercise subsequently passed](evidence/Stream-A-prepare-only-recovery-exercise-pass-2026-10-25.md):
healthy observation was inert, owner-loss recovery returned
`cancelled-prepared`, consumer-command count was zero, runtime custody cleared,
production remained healthy and F2/F6 were unchanged. This closes the
pre-effect recovery proof. It does not arm F6 or release D4/M3; fresh F2–F5,
an exact effectful activation/recovery card and a separate live approval still
precede consumer isolation and workload execution.
The missing fixed orchestrator is now source-complete on the platform branch
through `85c30e44`. The
[independent composition review](evidence/Stream-A-evaluation-composition-source-review-2026-10-25.md)
accepted direct F2/F3 row binding, fresh F4/F5/admission loading, guest-local
content-free D4/M3 verification, exact restoration checks and a hard-wired
no-CLI composition root. The focused suite passes 94/94. Read-only target
inventory and independent review support the 13-path inactive install card at
`62e1eb6f`; no composition code is installed and no live effect is released.

**October 24 M1 approval-plane checkpoint:** the
[permanent Yellow-only cutover](evidence/M1-permanent-yellow-cutover-result-2026-10-24.md)
passed. Only the Companion approval route now uses the independent broker and
dedicated ingress identity. The old approval service is disabled, both new
units are enabled, and service restart, execution-broker outage and LXC104
reboot recovery all passed. NPM and OPNsense retained their exact least-
privilege route, the signed-in read-only UI recovered, and the broker database
remained byte-for-byte unchanged with no pending or approved-unconsumed
request. This is a Yellow-only release: Red and management remain closed until
a separately proven passkey claim exists. Remaining M1 work is offline
demotion, revocation, expiry, stale-request and duplicate-consumption boundary
coverage; a real ceremony or grant is not implied.
The [first follow-on boundary suite](evidence/M1-approval-boundary-offline-coverage-2026-10-24.md)
closed that offline test gap with 40 broker and HTTP/socket passes, including
concurrent duplicate consumption, stale policy, demotion, capability
revocation and expiry. The subsequent
[two-file source promotion](evidence/M1-broker-revocation-source-promotion-result-2026-10-24.md)
passed: production now matches the reviewed repository core and approval
service, both brokers and the signed-in read path recovered, the same 40 tests
passed, and the consistent database checkpoints are byte-identical. No live
capability was revoked or granted. Red and management release remain closed
until their distinct passkey and ceremony gates pass.

**October 24 F2 result:** the approved exact-date preparation succeeded at
01:15, but the 01:20 final service returned NO-GO with bounded class
`FINAL_GUARD_SUBCHECK_FAILED` and no archive rows. The
[terminal record](evidence/F2-exact-cycle-no-go-2026-10-24.md) confirms no
scanner, lease or receipt remained, the spent timers were removed and
production postchecks passed. The installed wrapper still reduces all final
guard exceptions to one class, so another cycle is blocked on a per-subcheck
diagnostic correction and fresh proof. F3 cannot advance.
The platform owner's per-subcheck source correction at `770107df` now has a
[matching independent review](evidence/F2-final-guard-subcheck-correction-independent-review-2026-10-24.md):
candidate and live baseline hashes match the card, a clean-archive focused run
passed 24 tests with one expected macOS custody skip, and the owner reports
24/24 target-Linux passes. It is ready only for a separately approved inactive
two-file installation; no retry or timer follows automatically.

**October 18 lab-hours pilot checkpoint:** Jason approved up to 90 minutes of
daytime Aster/voice unavailability for a first supervised no-reboot pilot.
The combined 19-file Proxmox plus one-wrapper LXC110 packet from `b43d4971`
is installed **inactive** and passed 47 target-Linux synthetic tests; no
service was stopped. The platform owner has since produced an independent
deadline guardian and manual rescue, and Stream A verified the frozen
`dafc0332` source and four-file upgrade card `da082685` with 296 offline tests
(four expected Mac root-custody skips). Jason approved that exact inactive
upgrade; all four target hashes and 65 target-Linux tests passed, with
production unchanged. A later live 30-minute lab plus
15-minute restoration pilot has a separate approval and fresh News/backup,
operator, runtime and recovery gates. It tests known-consumer isolation and a
fixed in-guest model smoke, **not** recurring MacBook lab hours or continuous
host-wide GPU exclusivity. The [dated assessment](evidence/Lab-hours-acceleration-assessment-2026-10-18.md)
retains the review and measured counterexamples.
The first read-only live-source check failed on October 18 because the
completed 00:30 backup task had fallen out of Proxmox's current task listing;
the installed UPID pattern also rejected its valid trailing-colon form. The
platform owner replaced that source with bounded, durable journal proof in
`c66b9ae8`. Jason approved its separate four-file inactive installation;
installed hashes and focused Linux tests match, and the owner reports a
successful read-only current-cycle backup proof. The proposed six-minute
18:05 start window still cannot fit the implemented 30-minute lab plus
15-minute restoration profile. A new time-accurate live card, fresh gates
and separate approval remain necessary. No guardian was armed or production
service stopped.

**October 18 A1 interface checkpoint:** the platform owner corrected the
recovery-trigger/deadline ambiguity and versioned the callback as
`aster-a1-admission.v2`; Stream A's [client candidate](benchmarks/A1-full-path-admission-run-card-2026-10-13.md)
now requires that shape and refuses a batch or request reaching the recovery
trigger. The platform's typed pre-lease and fixed-file custody adapters are
offline, uninstalled and not connected to actual source-specific Proxmox,
TrueNAS or LXC observers. They do not yet authenticate the backup chain or
prove restoration time. The application-only drill and full Aster-path A1
benchmark remain BLOCKED. The [interface review](evidence/A1-admission-platform-interface-review-2026-10-18.md)
distinguishes completed source checks from the remaining live gates.

**October 17 evening correction:** the later supervised October 17 F2 guard
attempt returned NO-GO without any archive results. Its one-cycle approval
is spent and its recurring automation is now verified `PAUSED`. The normal
backup schedule continues; no F2 retry, full-stop drill or A1 benchmark is
scheduled for the following night. Source-only failure diagnostics and result
projection corrections did not lift these gates. On October 18, Jason approved
only the disabled diagnostic guard replacement. The platform owner's
[installed-path result](../../../services/local-ai-lease/F2-DIAGNOSTIC-DISABLED-INSTALL-RESULT-20261018.md)
and Stream A's independent hash, ownership, timer and no-receipt checks passed.
No archive scan ran in that installation, and F2 remains FAILED/UNKNOWN.
Jason then approved one conditional October 19 read-only F2 attempt and
subsequently an active daily schedule under the platform owner's revised
[F2 protocol](../../../services/local-ai-lease/F2-FRESH-CYCLE-SUPERVISED-SCAN-CARD-20261018.md)
at `42fa1308`. The existing Codex wake-up is verified active at 01:05
Vancouver daily. Each cycle checks fresh backup, TrueNAS, installed-source,
quiet-host, lease and operator gates; it may skip and never retries within a
cycle. It must pause after one complete three-archive success or a safety/
review condition. No scan result, receipt, drill or A1 benchmark is claimed
before actual evidence is retained.

**October 20 exact-cycle result:** both date-specific timers fired, but the
preparation service failed after five seconds and the final service failed
immediately. The [terminal record](evidence/F2-exact-cycle-no-go-2026-10-20.md)
contains no archive rows. Because the final generic error replaced the
earlier preparation state while unit output was suppressed, the exact failed
preparation sub-gate is unknown. Production postchecks passed and all F2
timers are disabled. F2 remains failed/unmeasured; no F3 release, drill or
A1 run follows. The bounded first-failure diagnostic correction is now
installed inactive with verified rollback and 10/10 target-Linux tests; it
does not repair the historical result. A fresh reviewed and separately
approved cycle is still required.
Jason has now approved and activated that fresh cycle for October 21. The
fixed-window coordinator is installed with verified rollback; preparation is
scheduled once at 01:15 PDT and the read-only scan once at 01:20, bounded by
01:40. A 01:42 observer is reconciliation-only. F2 remains open until the
actual terminal evidence contains exactly three valid exit-zero archive rows
and clean postchecks; no F3 or full-stop action follows merely from activation.

**October 21 exact-cycle result:** the prepare phase returned
[NO-GO](evidence/F2-exact-cycle-no-go-2026-10-21.md) and no archive scan or
result rows followed. Direct schedule/source reconciliation found two
incompatible assumptions in the pinned release: its 01:15 preflight required
the LXC110 mirror populated by the 02:00 task, and its 01:20 final call was
outside the 01:10–01:19 windows accepted by the final guard, observer and
producer. The spent exact-date timers were removed and production remained
healthy. The [internally consistent replacement](evidence/F2-final-minute-consistency-inactive-install-2026-10-21.md)
is now installed inactive with exact rollback custody and 33/33 target-Linux
tests. It removes the future-mirror dependency and aligns the final chain to
01:20/01:40. No timer, scan, receipt or lease followed. F2 and F3 remain
blocked pending a fresh measured result. Jason subsequently approved the
[October 22 exact-cycle activation](evidence/F2-exact-cycle-activation-result-2026-10-22.md):
date-specific 01:15 and 01:20 timers are active, recurring F2 timers remain
disabled, and a one-time observation-only reconciliation is due at 01:42.
Activation is not a pass; only three bounded exit-zero archive rows and clean
postchecks can complete F2.

**October 22 exact-cycle result:** preparation succeeded, but the final phase
returned [NO-GO](evidence/F2-exact-cycle-no-go-2026-10-22.md) after one second
with bounded class `FINAL_FAILED`. No archive row was produced and the scanner
did not run. The exact final-guard subcheck is unknown because the service
suppressed its internal error and the retained class is intentionally coarse.
The spent exact-date timers were removed, recurring timers remain disabled and
production postchecks passed. F2 and F3 remain blocked pending a more specific
bounded final diagnostic, offline and target-Linux proof, and a fresh reviewed
cycle.

**October 15 afternoon compatibility checkpoint:** Jason approved the
hash-pinned **inactive** full-stop candidate installation on Proxmox. The
installation result on the separate local branch `codex/aster-lease-compat`
(`services/local-ai-lease/FULL-STOP-COMPATIBILITY-DISABLED-INSTALL-RESULT-20261015.md`)
records 12 candidate Python modules and two heartbeat units at their pinned
bytes, preserved originals, target-Linux installed-path tests, unchanged old
controller/recovery/watchdog bytes, disabled/inactive timers and no lease or
lock. This closes the disabled-install/schema test gate, **not** the live
full-stop gate. The CLI effect paths remain hard-disabled. The current-cycle
retained archive receipt, independently active watchdog/recovery and exact
post-drill restoration remain unproved. A conditional, read-only archive
timing check is scheduled for October 16 at 01:10 Vancouver; it cannot write
the trusted receipt or launch a drill. Full-stop and A1 remain NO-GO pending
their distinct live admissions.

**October 15 preflight outcome:** The current 00:30 Proxmox backup and all
three 01:00/02:00/03:00 TrueNAS pulls succeeded. The protected nine-file A1
subset matched its prior Mac source snapshot after the 03:00 pull. The one-time
cold archive check passed LXC104, but the interrupted LXC110 scan has no
recoverable final exit status and LXC116 was not scanned. No installed
current-cycle retained integrity receipt or verified compatible full-stop
acquisition path was found. The [content-free preflight record](evidence/A1-2026-10-15-read-only-preflight.md)
therefore marks both full-stop and A1 **NO-GO for this cycle**. The
[03:40 post-window check](evidence/A1-2026-10-15-post-window-recovery-check.md)
then found no drill, unchanged active production services and pinned SYCL
artifacts, but still no compatible installed acquisition or trusted integrity
receipt. All three one-time checks are now paused. This is a hard evidence
gate, not a request for more lab time.

The [Stream A work cadence](Stream-A-Work-Cadence.md) separates continuous
offline/shared work from exclusive lab tests. The
[A1 private-subset scanner hardening](evidence/A1-subset-scanner-descriptor-hardening-2026-10-15.md)
closes an offline path-substitution race in its content-free observation
helper; it does not satisfy the source-bound admission gate. The proposed
03:15 Vancouver platform drill on 2026-10-15 was **not verified as scheduled**
and would be a
full-stop recovery drill only; its lease stops B60 inference and cannot run
the full Aster-path benchmark. The Stream A 03:40 automation was a read-only
post-window recovery check, not a test launcher; it ran once and is paused.
Continuous Stream A work remains active, and the A1 benchmark needs its
separate application-only lease and sidecar admission.
An [October 14 installed-path audit](evidence/Full-stop-lease-schema-mismatch-2026-10-14.md)
found that the existing manual full-stop controller writes a different lease
schema from the independent watchdog's strict decoder. Until a compatible
acquire path is installed and tested, the proposed live full-stop drill is
NO-GO regardless of the clock or backup completion.
The [measured archive-integrity timeout](evidence/Full-stop-backup-integrity-timeout-2026-10-14.md)
adds an independent NO-GO: the 43.585 GB LXC110 archive did not finish the
fixed 300-second check, so the planned 03:05–03:10 preflight cannot establish
current-cycle integrity. The platform owner has marked its proposed full-stop
card NO-GO pending a revised, measured integrity receipt and compatible
acquisition path. Neither read-only Stream A automation launches a drill.
The platform owner's later source-only retained-receipt adapter at `b5ec9eb2`
is reviewed and tested but not installed, enabled or wired into acquisition.
An [October 15 source-only sequencing review](evidence/Full-stop-retained-receipt-sequencing-review-2026-10-15.md)
also identifies the distinct pre-acquire backup and post-stop quiescence
decision points that the revised card must bind explicitly.
The 01:10 cold current-cycle scan was partial and target-Linux integration
remains open.
On October 15, Stream A implemented the missing source compatibility path on
the separate local branch `codex/aster-lease-compat` through `496b1136`.
Its `services/local-ai-lease/FULL-STOP-COMPATIBILITY-SOURCE-PACKET.md`
and `services/local-ai-lease/FULL-STOP-COMPATIBILITY-DISABLED-INSTALL-CARD.md`
specify the retained scan, fixed backup/runtime sources, pre/post-isolation
state transitions and target-Linux rollback checks. At that source checkpoint
the command-line paths were hard-disabled and nothing was installed; the later
inactive installation and target-Linux validation are recorded above. The
full-stop drill is still NO-GO pending a complete current-cycle trusted archive
receipt, independent recovery and a separately approved live run. The offline
suite ran 175 tests: 173 passed and two root-custody tests were skipped on macOS. The
code branch has not yet been reconciled into this Stream A branch or pushed.
The configured 00:30/01:00/02:00/03:00 backup schedules were checked read-only
on Proxmox and TrueNAS; this does not prove a given night's completion. The
platform owner's record reports one successful manual light lease, but the
controller is unscheduled and no
current lease is established for Stream A. The News/analysis reservation and
exclusive test access remain unverified.

The [2026-10-13 full-path admission card](benchmarks/A1-full-path-admission-run-card-2026-10-13.md)
pins the 20-case headless synthetic request boundary and fail-closed offline
preflight. The platform owner has installed an independent full-stop recovery
candidate disabled/inactive, but has not yet live-proven it. Jason approved a
separate [disabled application-controller installation](evidence/A1-application-controller-disabled-install-2026-10-14.md):
all 12 pinned files are on Proxmox, its watchdog units are disabled/inactive,
and no application lease exists. A subsequent
[disabled helper upgrade](evidence/A1-disabled-helper-upgrade-2026-10-14.md)
installed and hash-verified 24 pinned Proxmox/LXC110 files, retained the prior
Proxmox bytes for rollback, and left both heartbeat and watchdog units
disabled/inactive. The LXC104 A1 sidecar and dependency bundle
are also staged disabled. The live ingress effect, authenticated admission callback,
source-bound backup receipt and recovery behavior still need separate live
proof; installation does not admit a model call. The obsolete evening runner remains
disabled. The [isolated process contract](benchmarks/A1-isolated-process-contract-2026-10-14.md)
and [source inventory](benchmarks/A1-Aster-source-bundle-inventory-2026-10-14.md)
record the current admission gaps and establish that the first run, if
admitted, measures a pinned **Stream A candidate path**, not today's deployed
Aster binary.
An [independent source review](evidence/A1-live-drill-admission-gap-2026-10-14.md)
found that the installed drill entrypoint checks a prelease backup marker but
no fixed producer yet derives that marker from current-cycle backup sources.
The restricted Mini-to-host admission identity is also outside the disabled
install. Those are live-drill and benchmark gates, not installation defects.
An offline guarded Aster gateway candidate now pins the sealed 20-case wire
requests, separates ingress and isolated inner authentication, and supports a
durable one-attempt journal. The admission check requires those boundaries and
a common gateway topology for control and challenger. None of these source
tests proves a deployed test instance or a live independent restore; the A1
full-path run remains **BLOCKED**.

The native app now also needs the
[D3 integration gate](evidence/D3-native-app-integration-gate-2026-10-12.md):
the current AI-PAM app line and Stream A's manual Codex pilot have divergent
sources and shared-file edits. Do not install one line over the other.
An [isolated composite candidate](evidence/D3-composite-offline-candidate-2026-10-12.md)
now preserves the current OpenBao/auth source and passes offline tests. A
stable-signed release bundle and byte-verified signed copy of the
previous working app were prepared. Jason approved installing the composite
on the Mac mini. Its signed-in UI, read-only OpenBao status after passkey and
AI-PAM panel checks pass. One simple ordinary Aster question returned the
expected answer. [Natural refresh is now a monitored reliability check](evidence/D3-refresh-gate-reassessment-2026-10-12.md),
not a reason to hold unrelated Stream A work. The browser
Companion's existing OpenBao controls are
unchanged.
The manual Codex button is a Mac pilot, not the target user experience:
evidence-backed automatic handover is milestone 6, and it will not grant
tools or bypass privacy/approval policy.
The [later installed-bundle check](evidence/D3-composite-offline-candidate-2026-10-12.md#later-installed-bundle-drift-and-crash-check--2026-10-13)
records an app-owner replacement, an intermediate crashing build, and a
subsequent signed build observed working in ordinary use. The currently
installed executable no longer has the composite's recorded hash. The app
owner's release record pins the matching source and artifact; independent
reproduction of that build and long-term reliability remain open. Stream A did
not restore the older app. This does not change the manual-Codex HOLD or the
independent M1/M3 work queue.

The [app owner](../Aster-Unified-Voice-Service.md) later recorded the same
signed archive and executable as accepted on both Macs in commit `53717bb0`
after ordinary request, voice and OpenBao
status checks. This strengthens the ordinary Companion/voice acceptance; it
does not resolve the manual Codex pilot's exact manifest mismatch, verify a
new Codex consent/send, or enable automatic handover. Stream A retains those
as separate release gates.

## Where we are

The **historical version-16 Companion pilot** ran in ordinary mode with its
manual Codex screen hidden except for supervised experiments. Fourteen
earlier fictional turns plus one Nova process-interruption turn are recorded
as completed. A reviewed question reached subscription-backed Codex and its
**original** answer was recovered after a Companion restart; the
[one-attempt result](evidence/D3-active-turn-interruption-result-2026-10-09.md)
has a possible signal/completion race. No Aster tools or infrastructure
permissions were granted for those turns. The
[twelve-answer second pass](evidence/D3-existing-answer-second-pass-2026-10-09.md)
found eleven clear frozen-rubric matches and one qualified wording concern.
A [separate read-only review](evidence/D3-Orion-independent-review-2026-10-11.md)
judged the flagged Orion case a qualified pass; the other eleven were not
independently re-scored. The reviewed signed composite is now installed.
Its source and preceding app were pinned; Stream A independently checked
signed-in UI, fresh passkey/OpenBao status, AI-PAM and one ordinary answer.
The earlier predecessor has a documented sign-in bug. A
verified intact copy of the currently working installed app is now the local
rollback candidate; a restore-and-launch drill and off-site receipt remain
open.

This establishes a **bounded manual handoff**, not routine Ask Codex, automatic engine selection or a Codex sysadmin. The existing household/assistant path remains separate. Local Qwen's general-sysadmin trial was closed without promotion; that does not remove local models from cheaper or narrower tasks.

**2026-10-11 backend change:** read-only checks now find the B60 with a 32 GB
physical BAR and the accepted local 9B model served by llama.cpp SYCL FP16,
not Vulkan. The [current-runtime record](evidence/Stream-A-SYCL-runtime-reconciliation-2026-10-11.md)
pins the changed implementation for future routing measurements. No Stream A
qualified answer-quality or user-facing latency result for SYCL has yet been
established; D3 and M1 gates
do not change. The repository gateway prompt and current references contained
stale Vulkan claims; local corrections and dated evaluation copies are staged,
and a bounded live correction now aligns the deployed deterministic identity,
prompt and curated knowledge with 9B/SYCL. A service-account retrieval check
passes against the full refreshed 1,825-source snapshot. The deterministic
identity shortcut is now represented locally and the staged 199-test suite
passes. The Doctor reader was later transplanted with a 199-test hybrid pass;
the [branch gateway file now exactly matches the deployed file](evidence/SA0-gateway-UI-source-parity-2026-10-12.md). Eight of its nine directly imported local modules also match production; the [Lab Operations difference](evidence/SA0-gateway-module-parity-2026-10-12.md) is an uninstalled operator-only reconciliation candidate plus a now-corrected local 9B response label. This is source reconciliation, not a deployment or whole-application release; integration gates remain separate. Authenticated answer quality
is unverified.

## Remaining milestones, in delivery order

| Milestone | What changes for Jason | Evidence needed to finish | Current state |
|---|---|---|---|
| **1. Decide the limited manual Codex release (D3)** | A reliable, explicitly chosen “Ask Codex” path in the Mac Companion pilot, still without infrastructure tools. | Verify the installed composite's flagged UI and explicit consent without another unnecessary Codex question; retain a verified signed rollback and monitor session/Keychain behavior. A failed observation means **hold**, not repeated question trials. | **DEFERRED / SAFE HOLD.** Independent Orion judgment is a qualified pass, and [v16 completed nine natural persisted refreshes](evidence/D3-v16-natural-refresh-and-current-bundle-drift-2026-10-12.md). The supervised installed surface failed closed on an exact metadata-manifest mismatch without sending a question. The [priority reconciliation](evidence/D3-manual-pilot-priority-reconciliation-2026-10-25.md) records that the hidden manual button is no longer on the active critical path while NLU-based automatic directing is formalized. Resume only if Jason requests this fallback as a supported product path; do not repin or repeat questions merely to clear the row. Ordinary Companion reliability remains in scope. |
| **2. Complete normal Companion job handling (rest of D3)** | Jason can see a job continue/reconnect, distinguish busy, unavailable and quota states, and understand cancellation or an uncertain outcome. | Offline lifecycle tests and a small, separately reviewed ordinary-use check; preserve request IDs, never resubmit uncertain work, and keep basic Aster available when Codex/Mac/Internet fails. Follow-up context and notifications need explicit scope rather than being silently inferred from the pilot. | The [current source revalidation](evidence/D3-ordinary-job-handling-offline-revalidation-2026-10-25.md) passes all 60 native tests plus 66 targeted dependency-free delegation tests with five skips. The [live Companion window](evidence/D3-companion-test-window-2026-10-25.md) then passed two persisted-session relaunches, read-only OpenBao status, fail-closed recorded-request handling and one exact ordinary Aster response in 2.8 seconds. AI-PAM Management remains an inconclusive accessibility/display observation, and the durable failure categories remain confined to the hidden manual path. General Codex intake/notification are **not released**. |
| **3. Establish the authority boundary before connected tools (M1 + D4 prerequisite)** | Codex may ask for narrowly scoped read-only evidence; it cannot obtain permissions by choosing a route. | Verify AI-PAM caller binding, demotion/revocation, expiry, stale policy, duplicate approval consumption and recovery; register each read-only target and keep secrets out of model context. Any connected capability has its own deployment gate. | **SYNTHETIC AUTHORITY PROOF COMPLETE.** The permanent independent route passed service restart, execution-broker outage and LXC104 reboot recovery. Reviewed broker source covers caller binding, demotion, capability revocation, expiry, stale policy, duplicate consumption and UI recovery. The exact [passkey mapping](evidence/M1-independent-ingress-passkey-install-result-2026-10-25.md) accepts only the reviewed Aster WebAuthn ACR. The final [live Red/management ceremony](evidence/M1-red-management-ceremony-result-2026-10-25.md) recorded a one-second-old passkey claim, consumed one hash-bound fictional Red request, denied its duplicate, and wrote one same-state management audit event. The read-only verifier proved exactly one terminal request and four ordered audit rows with no grant, policy, service, agent or global-switch drift; production remained healthy. The optional session-visibility UI remains undeployed, but freshness is now proven at the broker boundary. This evidence does not release generic Red or management actions: each real connected capability still needs its own least-privilege registration, deployment and effect gate. |
| **4. Prove useful read-only sysadmin investigation (first D4 role)** | Aster can hand a real but bounded diagnostic question to Codex and explain findings, uncertainty and evidence. | Representative incidents, provenance and freshness, actual read-only tool behavior, independent technical postchecks, and a clear pass/fail rubric. No fix or generic shell authority follows from diagnostic success. | The offline incident/evidence engine, private journal, terminal-answer lineage, qualification-gated plan and label-free executor boundaries exist. Attempts 5–7 closed response-contract and validator gaps. [Attempt 8](evidence/D4-tool-free-development-attempt-8-result-2026-10-24.md) passed structurally but scored 6/12 across all blind-review dimensions. [Attempt 9](evidence/D4-tool-free-development-attempt-9-result-2026-10-24.md) also passed structurally, but candidate-F scored 0/12 across all dimensions because the response representation conflated diagnostic checks with post-change verification and did not enforce complete evidence lineage. Candidate-G remains exact and unspent but candidate-H is the current proposed workload under its own future approval. The endpoint-retaining lease implementation is installed inactive and its prepare-only recovery exercise passed with zero consumer commands. The revised candidate-H/M3 effect card has a [passing independent static review](evidence/Stream-A-candidate-H-F6-static-card-review-2026-10-25.md), and the missing fixed orchestrator now has a [passing source review](evidence/Stream-A-evaluation-composition-source-review-2026-10-25.md) with 94/94 focused tests. Its exact inactive installation remains pending; fresh F2–F5 evidence and a separate live activation/model-call approval still precede any consumer stop or model call. |
| **5. Qualify one supervised repair class (later D4/SA4)** | Only an exact reversible fix can be proposed and, after Jason's specific approval, carried out. | Precondition/checkpoint, exact target and action, AI-PAM grant, independent postcheck, rollback, uncertain-outcome reconciliation and emergency stop. | Not authorized. |
| **6. Add low-resource automatic handover (M3–M6)** | Routine requests stay on deterministic/local paths; only requests that need stronger capability go to Codex or another approved provider, with privacy and cost controls. | Stable Decision/Capability contracts, representative routing labels, calibrated abstention, shadow comparison, measured latency/privacy/cost, and one evidence-backed promote-or-reject decision. The first route is read-only; a route never grants tools. | Contracts and historical baselines exist. The historical full-file-pinned probe remains frozen; an [explicit offline v2 component-pinned probe](evidence/M3-selector-pin-drift-2026-10-11.md) passes synthetic conformance but does not establish routing quality. The [9B/SYCL development test](experiments/m3-9b-sycl-routing-compatibility/RESULT-V4-2026-10-12.md) achieved valid format on 30/30 but expected-route agreement on only 18/30, with calendar, mixed and private-context gaps. No routing promotion. Automatic routing and Learning Plane promotion are not live. |

The previously implicit NLU stage now has an explicit
[request-interpretation boundary](NLU-Selector-Boundary.md). Its content-free
contract separates family, sensitivity, capability needs and ambiguity from
provider selection and AI-PAM authority; the expanded interpretation/route
semantic suite passes 11/11. This is
an offline interface only. The independent labelled holdout, calibrated
abstention and shadow comparison remain open, so automatic routing stays off.
The downstream selector now also emits a separate
[digest-bound route proposal](evidence/M3-NLU-route-lineage-boundary-2026-10-24.md)
with consistent backend/egress semantics, expiry and no authority. The expanded
focused suite passes 11/11, including personal-data cloud denial in the initial
profile. No selector is deployed and no route is promoted.
The NLU boundary now also has a
[pinned dimensional development scorer](evidence/M3-NLU-development-scorer-2026-10-24.md).
Its 24 exposed synthetic cases and 10/10 scorer tests separately measure family,
sensitivity, capabilities, ambiguity, disposition and reason, including privacy
underclassification and unsafe false routing. This closes the development-tooling
gap only. A new
[content-free holdout custody boundary](evidence/M3-NLU-holdout-custody-boundary-2026-10-24.md)
pins 36 opaque cases balanced across all six families, four distinct roles and
the required contract/scorer/threshold/non-overlap digests; its eight tests pass.
The [threshold-policy boundary](evidence/M3-NLU-threshold-policy-boundary-2026-10-24.md)
now requires the exact frozen policy artifact alongside a sealed release and
rejects holdout-informed selection, changed bytes and authority claims. Its
content-free selector freezes a registered policy only when all constraints
pass; 36 focused NLU tests pass. The template deliberately leaves quality,
coverage and sample-size acceptance values unset. No cases, labels, calibration
evidence or selected threshold exist. Independent constraint acceptance, case
creation, calibration, sealing and no-effect shadow evidence remain open before
any automatic handover. A new
[content-free calibration custody boundary](evidence/M3-NLU-calibration-custody-boundary-2026-10-24.md)
now binds future opaque calibration cases to the registered policy's sample
minima and exact candidate without inventing values; 42 focused NLU tests pass.
Numeric constraint acceptance, role assignment and any case/label creation are
still separate gates. A separate
[S0-only no-effect shadow boundary](evidence/M3-NLU-no-effect-shadow-boundary-2026-10-24.md)
binds future opaque comparisons to the exact frozen policy and requires no
execution or provider egress. A later
[non-vacuous policy correction](evidence/M3-NLU-nonvacuous-policy-boundary-2026-10-24.md)
rejects zero coverage and a 100% selective-error allowance. The subsequent
[holdout artifact-binding correction](evidence/M3-NLU-holdout-artifact-binding-boundary-2026-10-25.md)
requires exact contract, scorer, policy and development non-overlap receipt
bytes rather than trusting digest-shaped claims. The later
[calibration exact-release correction](evidence/M3-NLU-calibration-exact-release-binding-2026-10-25.md)
requires the policy-bound bytes to decode to the manifest under validation. A
[duplicate-key JSON correction](evidence/M3-NLU-duplicate-key-boundary-2026-10-25.md)
then makes threshold policy, calibration score and exact-release parsing
unambiguous. A subsequent
[shadow artifact-binding correction](evidence/M3-NLU-shadow-artifact-binding-boundary-2026-10-25.md)
requires each opaque shadow interpretation/proposal digest to match its exact
content-free artifact; the focused NLU suite now passes 52/52. The shadow
artifact remains an empty template, not collection approval or a route release.
The later [shadow semantic artifact correction](evidence/M3-NLU-shadow-semantic-artifact-boundary-2026-10-25.md)
rejects arbitrary digest-matching JSON and verifies exact contract shape,
candidate pins, interpretation/proposal lineage, route semantics and the
personal-cloud prohibition. The current dependency-free NLU suite passes
97/97; no shadow collection is authorized.
An [initial policy decision draft](evidence/M3-NLU-initial-threshold-policy-decision-draft-2026-10-25.md)
proposes zero privacy/unsafe failures, at most 10% selective error, at least 60%
coverage and 60 balanced calibration cases. The values remain unaccepted and
cannot be registered until an exact candidate and sealed calibration release
exist. A subsequent
[threshold-enforcement correction](evidence/M3-NLU-unrounded-policy-enforcement-2026-10-25.md)
applies those future constraints to the exact computed ratios and rounds only
the review output, closing a boundary case in which report rounding could admit
an out-of-policy candidate. The later
[development JSON ambiguity correction](evidence/M3-NLU-development-JSON-ambiguity-boundary-2026-10-25.md)
rejects repeated object keys at the fixture, run and manifest boundaries without
repinning existing evidence. A new
[candidate-bundle custody boundary](evidence/M3-NLU-candidate-bundle-boundary-2026-10-25.md)
then gives the previously arbitrary candidate digest a content-free exact
engine/policy/contract/adapter/runtime manifest, consistent egress and explicit
no-tool/no-authority semantics. The following
[calibration candidate-binding correction](evidence/M3-NLU-calibration-candidate-binding-2026-10-25.md)
requires the calibration gate to validate that exact sealed manifest and bind
its bytes through the registered policy. The equivalent
[shadow candidate-binding correction](evidence/M3-NLU-shadow-candidate-binding-2026-10-25.md)
preserves that exact identity through the later S0-only comparison. The
[holdout candidate-binding correction](evidence/M3-NLU-holdout-candidate-binding-2026-10-25.md)
extends it into independent qualification. The focused NLU suite now passes
63/63. A later
[machine-readable policy proposal](evidence/M3-NLU-machine-readable-policy-proposal-2026-10-25.md)
freezes the proposed numeric decision at digest `2e0def84…64a3d` while requiring
a separate exact acceptance record before status can become `accepted`; the
focused NLU suite then passed 68/68. No candidate has been selected or sealed
and no holdout was opened.
A subsequent
[deterministic registration gate](evidence/M3-NLU-policy-registration-gate-2026-10-25.md)
requires the exact accepted decision, sealed candidate and matching sealed
calibration release before constructing a registered policy; it rejects the
current proposal by design. A subsequent
[registration artifact integrity boundary](evidence/M3-NLU-registration-artifact-integrity-2026-10-25.md)
adds exact envelope validation, duplicate-key rejection, deterministic
serialization and owner-only no-overwrite persistence. The focused NLU suite
then passes 74/74. A following
[exact owner-acceptance boundary](evidence/M3-NLU-exact-owner-acceptance-boundary-2026-10-25.md)
so registration reconstructs an accepted decision only from the exact proposal
and a unique-key, self-hashed acceptance record bound to those proposal bytes;
it no longer trusts an arbitrary acceptance digest. The focused NLU suite now
passes 78/78, including an owner-only no-overwrite derivation CLI. Jason has
now [accepted the exact proposal](evidence/M3-NLU-owner-policy-acceptance-2026-10-25.md).
The recorded acceptance artifact is bound to the proposal bytes at SHA-256
`96d7f475…fe6cc`, and deterministic derivation produces the accepted decision
artifact at SHA-256 `8ef60a8b…614da`; its focused dependency-free verification
passes 68/68. This accepts only the evaluation constraints. At that acceptance
checkpoint no candidate, calibration set, registered threshold, shadow route
or execution authority had been sealed or enabled.
The existing Qwen3.5-9B Q4_K_M model and accepted SYCL profile are now also
[sealed as an exact local evaluation candidate](evidence/M3-NLU-local-candidate-seal-2026-10-25.md)
with a strict no-tool adapter. Read-only live hashes matched the model and
runtime profile, and the dependency-free focused NLU suite passes 74/74. This
selects only what calibration will measure; it does not promote the candidate
or enable routing. The next M3 gate is independent custody and review of 60
synthetic calibration cases, ten per family, before a lease-protected model run.
That gate now has an
[approval-ready creation card](evidence/M3-NLU-calibration-creation-card-2026-10-25.md)
fixing the three distinct roles, privacy/non-overlap rules, owner-only raw
custody and exact stop conditions. It is now complete: separate fresh contexts
created 60 private synthetic cases, performed blind pre-model label review and
derived the byte-verified content-free release. The
[custody](evidence/M3-NLU-calibration-case-custody-receipt-2026-10-25.md),
[label review](evidence/M3-NLU-calibration-label-review-receipt-2026-10-25.md)
and [release](evidence/M3-NLU-calibration-scoring-release-receipt-2026-10-25.md)
receipts bind the source and release without exposing text or labels. The exact
accepted policy is now [registered and bound to a preregistered binary route
score](evidence/M3-NLU-calibration-registration-and-score-boundary-2026-10-25.md),
and the dependency-free NLU suite passes 92/92. The
[60-case live run card](evidence/M3-NLU-calibration-run-card-2026-10-25.md)
is the next gate. No model call, threshold selection, holdout access, shadow
collection or routing change has occurred.
A subsequent [holdout calibration non-overlap correction](evidence/M3-NLU-holdout-calibration-nonoverlap-boundary-2026-10-25.md)
now requires the future independent holdout to bind separate exact receipts for
zero overlap with both the development set and the newly sealed calibration
set. Both receipts have fixed semantics and must describe the same 36-case
subject under a fifth independent non-overlap-review role. The dependency-free
NLU suite passes 96/96. No holdout content has been created or opened.
The [conditional holdout creation card](evidence/M3-NLU-holdout-conditional-creation-card-2026-10-25.md)
now fixes those five roles, both exact exclusion sets and private custody, but
it cannot activate unless calibration first freezes a valid threshold. A
calibration rejection expires the card unused.
The calibration runner now also has a
[strict wall-deadline correction](evidence/M3-NLU-calibration-deadline-boundary-2026-10-25.md):
it shortens each request timeout to the remaining 1,200-second budget, starts
no request after expiry and returns nonzero while preserving a partial run for
reconciliation. The dependency-free NLU suite passes 100/100. No live model
request or lease followed.
The subsequent
[durable attempt-journal correction](evidence/M3-NLU-calibration-attempt-journal-boundary-2026-10-25.md)
reserves owner-only evidence before inference and records each opaque attempt
start and completion durably before proceeding. An interrupted request is now
identifiably uncertain and cannot be replayed. The dependency-free NLU suite
passes 104/104; the live gates are unchanged.
The scorer now also
[requires semantic journal-to-run agreement](evidence/M3-NLU-calibration-journal-score-binding-2026-10-25.md)
and binds the exact journal digest into the threshold-selection input. The
dependency-free NLU suite passes 106/106. A journal can no longer exist merely
as an ignored sidecar.
The [LXC110 staging boundary](evidence/M3-NLU-calibration-LXC110-staging-boundary-2026-10-25.md)
initially fixed a minimal ten-file packet, persistent owner-only location,
content-free return path and retain-on-uncertainty cleanup rule. This avoids
exporting the local service key and keeps labels on the Mac. It is an offline
plan only; nothing has been staged. A read-only LXC110 preflight found the
target path unused, Python 3.13.5 available, the key file mode `0600` without
reading it, the accepted service active and adequate disk space.
The exact packet is machine-readable and fail-closed. Its validator
requires the exact staged names and byte-verifies opened regular files
without following symlinks; five focused tests and the full 111-test
dependency-free NLU suite pass. The
[actual Mac source packet](evidence/M3-NLU-calibration-source-packet-validation-2026-10-25.md)
also passes 10/10 byte verification. A later
[llama response-envelope compatibility correction](evidence/M3-NLU-llama-response-envelope-compatibility-2026-10-25.md)
prevents ordinary accepted `usage`/`timings` metadata from invalidating every
classification while still rejecting unknown metadata and retaining none of
it. The superseded ten-file packet passed at 93,612 bytes but failed closed
during its first LXC import check because it omitted `nlu_candidate_bundle.py`.
The [dependency-closure correction](evidence/M3-NLU-staging-dependency-closure-correction-2026-10-25.md)
adds the one missing local validator dependency. The corrected eleven-file
packet passes at 98,414 bytes with manifest SHA-256
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`, and
the full NLU suite passes 126/126 in the pinned Pydantic 2.13.4 environment.
The later
[staged-custody validator](evidence/M3-NLU-staged-custody-validator-boundary-2026-10-25.md)
enforces root ownership, `0700`/`0600` modes, the exact manifest name set and
absence of outputs or extra files.
The [inactive staging card](evidence/M3-NLU-calibration-inactive-staging-card-2026-10-25.md)
removes an unnecessary exclusive-window dependency: the inert eleven-file
packet may be copied and byte-verified before lab hours under its own bounded
approval, while the compatible lease and all runtime/recovery gates still
remain mandatory before the first model request. The first ten-file staging
attempt failed closed before rename and removed its LXC path. The corrected
packet subsequently [passed inactive staging](evidence/M3-NLU-calibration-inactive-staging-result-2026-10-25.md):
11/11 inputs, 98,414 bytes, exact root-only custody and target imports. No
runner, output, lease or model request exists. Live calibration remains gated
by an effectful compatible lease and its approved window.
The later [post-journal deadline correction](evidence/M3-NLU-post-journal-deadline-correction-2026-10-25.md)
found that the runner's request timeout could become stale while the durable
attempt-start row was flushed. Commit `682608d2` recomputes the budget
immediately before transport open and starts no request after expiry; 116
dependency-free tests pass. The corrected packet then
[passed its bounded inactive replacement](evidence/M3-NLU-deadline-correction-inactive-replacement-result-2026-10-25.md):
all 11 exact inputs match the new manifest, the run directory is root-only,
the generated bytecode cache was moved into the rollback checkpoint, and no
output, runner process, lease or model request exists. The accepted llama
service stayed active. Live calibration remains separately gated.
The [combined static readiness check](evidence/D4-M3-combined-evaluation-static-readiness-2026-10-25.md)
also reconfirms candidate-G's exact 11-file package and the staged M3 packet.
Both workloads are ready at the file/test boundary; F2/F3 and the platform's
effect adapter/recovery card remain the live dependencies.
The platform owner's first explicit effect entrypoint at `c3b316ab` passed its
own 30 tests but was [rejected before installation](evidence/Stream-A-evaluation-lease-effect-entrypoint-review-2026-10-25.md):
it pins the superseded M3 manifest, conflicts with the installed four-file
baseline, does not enforce exact schemas for every phase, and accepts weakly
custodied intent files/arbitrary state paths. The exact regressions are with
the platform owner. The inert library and M3 packet remain unchanged.
The final platform correction at `ae56046b` plus card commit `d2a32785` closes
those source and transaction gaps. Its clean archive passes 32/32 tests and
the live target exactly matches the required four-file prestate. The bounded
one-replacement/two-addition inactive upgrade received exact approval, but its
[target installation failed closed](evidence/Stream-A-evaluation-lease-effect-entrypoint-install-no-go-2026-10-25.md)
after 32/32 tests and installed imports passed. The real disabled wrapper
created `__pycache__` because it invokes Python without `-B`, violating the
card's exact-directory postcondition. Automatic rollback restored the original
four-file baseline, retained the root-only checkpoint and left no state, lock
or service change. The platform owner has the one-line wrapper correction and
regression requirement. Platform implementation `b18302f3` and card metadata
`6bf5f252` now provide that correction: the wrapper uses Python `-B`, the card
pins its new hash, and an independent clean archive passes 33/33 tests,
including the real no-bytecode wrapper regression. The corrected transaction
then [passed inactive installation](evidence/Stream-A-evaluation-lease-effect-entrypoint-install-no-go-2026-10-25.md)
after two packaging checks failed closed and restored the original baseline.
The final hierarchy-preserving packet passed 33/33 target tests, installed
imports, disabled wrapper execution, exact hashes/custody and the no-bytecode
postcondition. The old contract checkpoint is retained, the lease controller
is `ready`, production is healthy, and no state, lock, effect or model request
exists. The next live dependency is the independent watchdog/recovery
activation boundary plus fresh F2/F3/F4 evidence and a separate run approval.
The platform's first watchdog activation boundary at `5d4735c1` is
[not yet implementation-ready](evidence/Stream-A-evaluation-lease-watchdog-activation-review-2026-10-25.md):
no watchdog or owner-heartbeat units/wrappers exist, no root-custodied process
input binds lease identity and generation, the watchdog CLI remains
source-only, and no constrained recovery executable binds its decision to the
exact four-consumer restore. F6 is NO-GO pending a hash-pinned inactive packet
and target tests; nothing has been armed. The first implementation packet at
`8fa6d36f` adds the missing artifacts but is also rejected before installation:
its timer self-renews owner liveness without observing the owner, stale owner
heartbeats fail closed instead of recovering, uncertain restore exits zero,
and its restore observation has no constrained fresh writer or lease binding.
The second packet at `23602180` adds process identity and a fixed observer but
is rejected too: two fixed observer commands are absent from the live LXC110,
expired owner heartbeats still remain present, no persistent evaluation-owner
process exists to bind the new identity, and watchdog status remains unwritten.
The third packet at `3e843a8e` closes those gaps but still equates render-node
presence with the accepted GPU holder, hardcodes the resulting holder, has an
incorrect artifact count and leaves the active observer without an explicit
authorization flag. The fourth packet at `021cab2f` corrects those points and
its exact GPU-holder contract matches a live read-only host scan, but its
observer wrapper discards all command-line arguments. The watchdog's required
identity and authorization flags never reach the observer, so recovery cannot
run. That final measured integration regression is with the platform owner.
The fifth packet at implementation `780c33e2` and card `75b423d4` fixes the
wrapper and adds a real copied-wrapper regression. Independent review matched
all thirteen hashes and passed 51/51 clean-archive tests. Its approved
[inactive installation](evidence/Stream-A-evaluation-watchdog-inactive-install-2026-10-25.md)
then passed 51/51 target-Linux tests, installed imports, inert wrapper checks,
static unit validation and independent rehash. All five units/timers remain
disabled/inactive and no lease, identity, heartbeat, observer output or other
runtime state exists. F6 arming remains unapproved. The current adapter also
combines lease creation with immediate consumer masking/stopping, so a new
source-only acquire-only/start split is required before the intended
healthy-lease read-only gate can exist.
The platform owner's first pure endpoint-retaining lease candidate at
`44b26e16` passed its own 7/7 tests and names the correct live backend and News
timers, but Stream A's
[independent review](evidence/Stream-A-evaluation-lease-platform-candidate-review-2026-10-25.md)
rejected it before any installation or effect. Its restoration check
contradicts endpoint retention, its deadline check does not bind the fixed
90-minute window, its outcome check does not independently bind lease identity,
and it conflates registered targets with observed post-quiescence state. The
platform owner then closed those gaps and two follow-on fail-open cases in
`024f3c06`. The same independent review now accepts that pure contract after
10/10 exact-archive tests and isolated compilation. It still has no effectful
adapter or live entry point. Candidate-G and M3 remain unspent pending the
adapter, watchdog/target proof, installation decision and fresh F2/F3 evidence.
The platform owner's first source-only effect adapter at `6e29f0e8` is also
[rejected before installation](evidence/Stream-A-evaluation-lease-adapter-review-2026-10-25.md).
It declared `RUNNING` before observed quiescence, did not bind the recovery
baseline to the exact four consumers, and left watchdog inputs independent of
durable lease identity. The correction request and direct failure-test
requirements are with the platform owner; the host remains unchanged.
| **7. Operational graduation (M7/SA5)** | Jason can trust the *specific* demonstrated roles in normal use, with recovery and clear explanations. | Independent critical-path passes, degradation/restore checks, monitoring, documented limits and Jason's acceptance. This is role-specific, not a claim of universal autonomous administration. | Open. |

The [M1 inactive installation](evidence/M1-independent-ingress-inactive-install-result-2026-10-24.md)
passed its exact hash, Linux import, unit, identity and production-health checks
before the later supervised pilot and permanent release.
A [supervised zero-overlap cutover card](evidence/M1-independent-ingress-zero-overlap-cutover-card-2026-10-24.md)
now fixes the exact path split, 9121 firewall scope, service order, denial and
execution-broker-independence checks. It preserves chat, voice and OpenBao on
9120 and covers both Companion clients without an app rebuild. The first
cutover would be explicitly Yellow-only: Red and management remain denied until
a real passkey-specific claim is proven. No live cutover is authorized yet.
The [static preflight](evidence/M1-zero-overlap-cutover-static-preflight-2026-10-24.md)
was GO. The [first supervised pilot](evidence/M1-zero-overlap-cutover-first-pilot-result-2026-10-24.md)
first found the parent-runtime-directory group defect, then proved the corrected
identity boundary and found a temporary firewall sequence error before any
authenticated request. Each attempt restored NPM, firewall, services and the
empty broker database. The final [supervised pilot passed](evidence/M1-zero-overlap-cutover-pilot-pass-2026-10-24.md)
with sequence 2199, an authenticated content-free Companion read and execution-
broker independence, then restored the exact database hash and old route.
That pilot evidence is now historical input to the completed permanent cutover.
A [pinned permanent-cutover card](evidence/M1-permanent-yellow-cutover-card-2026-10-24.md)
defined the two boot-enabled release units, exact sequence-2199 firewall
placement, NPM route, zero-overlap service order, one LXC104 reboot, recovery
proof and restrictive rollback. The approved
[deployment passed](evidence/M1-permanent-yellow-cutover-result-2026-10-24.md)
and the independent route is now production state.

Milestones 3 and 6 proceed independently of D3 session aging. Connected tools wait for milestone 3; automatic routing does not need to be built before a limited manual Codex release. The earlier SA0–SA5 table records operational requirements and historical Qwen work; it is **not** a second obligation to rerun the closed Qwen general-sysadmin trial. Its still-applicable authority, investigation, repair and acceptance checks map into milestones 3–7.

The [Aster Ask development benchmark](benchmarks/ask-routing-development-v1/README.md) now pins the 9B/SYCL run, model/runtime/prompt provenance and an independent offline scorer for future local or Codex backends. The Codex score is **pending** because the D3 manual pilot used different questions and has no equivalent routing output. The 30 exposed synthetic cases are useful for regression checks; a new human-labelled holdout and shadow evidence still gate any automatic handover.
The same published cases now have a pinned **30/30 existing lexical-rule
control**. Those rules and cases were authored together, and their Mac latency
cannot be compared with the B60 request timing. The control confirms that a
future local stack must add measured value beyond simply reproducing these
examples; it is not an independent quality or deployment result.
The October 17 [scorer hardening](benchmarks/ask-routing-development-v1/README.md)
rejects decision fields on invalid attempts and nonnumeric run timings while
preserving both baseline scores. This protects the evidence format; it does
not advance the independent-label or shadow-routing gate.
An [offline Decision contract correction](evidence/M3-decision-sensitivity-boundary-2026-10-16.md)
now rejects a proposed capability whose registry sensitivity exceeds the
request sensitivity. This closes a synthetic compatibility-check omission;
it neither establishes request classification accuracy nor grants routing or
tool authority.
A separate [offline label-boundary correction](evidence/M3-private-category-label-boundary-2026-10-16.md)
requires calendar and personal development-data categories to remain personal
and local-only even when their capability lists are incomplete. It changes no
live route or egress policy.
The typed Decision contract now also enforces a
[status/reason boundary](evidence/M3-decision-status-reason-boundary-2026-10-21.md):
supported outcomes cannot carry a policy-denial reason, and denial cannot be
described as supported. Focused tests cover every accepted combination and
contradictory examples. This improves audit semantics only; routing remains
disabled and the historical reviewed-source pin was not repinned.
The typed Outcome contract now likewise enforces an
[outcome status/verification boundary](evidence/M3-outcome-status-verification-boundary-2026-10-22.md):
only a completed attempt may claim fixture conformance, while every failed,
denied, expired, cancelled or budget-exceeded attempt is recorded as not
executed. The isolated contract and evidence suites passed 14/14 without
repinning the historically drifted adapter source. This protects later
evidence semantics; it does not establish routing accuracy or enable routing.
The append-only evidence store now also binds a
[completed outcome to its registered run budget](evidence/M3-outcome-budget-lineage-boundary-2026-10-23.md):
tool-call count must match the frozen Decision, and elapsed/output measurements
must remain within the registered limits. Focused evidence suites passed 27/27;
the historically drifted source pin was not changed. This prevents a producer
from labelling an over-budget synthetic run conformant, but supplies no routing
accuracy or promotion evidence.
The evidence store now also binds a
[recorded Outcome to the registered Decision's executable class](evidence/M3-decision-outcome-lineage-boundary-2026-10-24.md).
A denied, clarify, abstain or unsupported Decision can no longer acquire a
completed fixture-conformance Outcome; synthetic rejected/accepted examples
and the focused contract/evidence suites passed 30/30. The historical adapter
pin remains drifted and unchanged. This improves lineage only; routing remains
disabled and no promotion follows.

The first [six-case synthetic completed-answer probe](experiments/a1-9b-synthetic-answer/RESULT-2026-10-12.md)
used the accepted 9B/SYCL service after the platform owner's light lease was
released. All six fictional requests returned text, with a 1.123 s median
request-to-terminal time; a clear calendar reasoning error and other rubric
omissions mean answer quality remains unqualified. The six exposed cases and
nonblind author review do not establish a useful-answer rate, class budget or
automatic routing gate. The service remained healthy with no tools or runtime
changes.

The [completed-answer control profile](benchmarks/completed-answer-control-measurement-profile-v0.md)
now fixes how future Aster-path timing, timeouts, paired candidates and blinded
rubric reviews will be recorded. It sets no release budget from the six-case
probe. B60 has adopted the common development capture interface; its wrapper
has now reconciled the Aster capture source pin and passed its focused bridge
tests. Fresh cases,
independent labels and class-specific waiting-time limits remain open.
The calendar error also motivated an [offline deterministic-overlap prototype](hypotheses/H-A1-calendar-overlap-deterministic-2026-10-12.md).
Its six developer-authored tests pass, but it has no live calendar adapter,
independent accuracy estimate or routing authority.
A [private review handoff and ASGI clock check](evidence/A1-private-review-and-asgi-clock-2026-10-12.md)
now make the answer-review and request-timing paths reproducible offline. The
packet has an AI-only development review (2/6 all-rubric passes), not human
adjudication; the in-process clock is not a live Aster-path latency baseline.
Neither changes the automatic-route gate.
The [fresh 20-case assistant-answer holdout](benchmarks/answer-holdout-release-v1-2026-10-12.md)
was sealed in owner-only local custody with a separate AI review and zero
material overlap with the six exposed development cases. A first 9B invocation
returned a 20-row envelope but the Mac sandbox denied the final local write,
so **no answers or score were retained**. The [failure record](experiments/a1-answer-holdout-v1/RESULT-FAILED-2026-10-12.md)
closes v1 without replay. The transport now proves local writability before a
model call and seals stdout before parsing. A [fresh v2](benchmarks/answer-holdout-release-v2-2026-10-12.md)
was sealed with 20 independently AI-reviewed fictional cases and a bounded
[run card](experiments/a1-answer-holdout-v2/RUN-CARD-2026-10-12.md). One
accepted-9B direct-backend attempt produced 20/20 responses; two blind AI
reviews agree on [14/20 full-rubric passes](experiments/a1-answer-holdout-v2/RESULT-2026-10-12.md),
including 0/2 calendar-plus-web. Direct-backend median was 1,178.5 ms, not
native Aster latency. Labels are AI-authored and AI-reviewed; recoverable
backup, human adjudication and live Aster-path measurement remain open. The
[backup check](benchmarks/A1-protected-evidence-backup-plan-2026-10-12.md)
found no Time Machine destination and no prior coverage under the documented
restricted TrueNAS Mac pull. Jason approved an exact
[owner-only backup-tree copy](evidence/A1-protected-evidence-local-copy-2026-10-12.md),
which matches all nine source file hashes and inherited restricted
read-only backup ACLs. The normal TrueNAS pull and [isolated restore/re-score](evidence/A1-protected-evidence-TrueNAS-restore-2026-10-13.md)
passed on 2026-10-13. The same record verifies the current encrypted off-site
copy by a byte comparison; it does not establish historical-version recovery
for these files. No
route or tool is promoted. The platform project's SA3 **sysadmin**
holdout is separate and has ended without promoting local Qwen to a Codex
sysadmin role.
The MacBook B60 branch has now [received and independently checked the public
A1 v2 score exports](benchmarks/B60-coordination-interface-2026-10-12.md),
without receiving private cases or reproducing model judgments. The
[owner-held candidate contract](benchmarks/A1-v2-candidate-adapter-and-admission-2026-10-12.md)
keeps any later paired run on the Mini and records why candidate staging,
the whole-host lease and full Aster-path timing remain blocked.
An [in-process synthetic clock pair](../../../scripts/aster-adaptive/synthetic_client_clock.py)
now joins the B60-supplied client timing producer with Aster's ASGI clock on
fictional fixtures. Its tests show that gateway completion without client
display is censored and that no raw answer enters timing records. It does not
measure the native Companion or establish answer usefulness. Candidate,
lease and independent-label gates remain open.
The [proposed class-specific sample policy](benchmarks/A1-class-qualification-sample-policy-v0.md)
separates regression evidence from qualification and requires independent
labels and a frozen per-class bar before a challenger can earn a route.

The existing D4 aggregate Doctor adapter now closes a file-open race, rejects
symlinked or writable reports, and fails closed on malformed status types; see
the [live boundary record](evidence/D4-doctor-adapter-live-boundary-2026-10-11.md).
It remains aggregate-only and does not alter the connected-tool gate or release status.

The existing ARR aggregate report can answer a simple named-service status
question locally. Its [offline file-boundary hardening](evidence/ARR-report-file-boundary-2026-10-09.md)
does not turn that question into a Codex sysadmin role or grant access to a
repair candidate.
The [malformed-input review](evidence/ARR-report-malformed-input-boundary-2026-10-11.md)
also found two local fail-closed gaps and a path-bearing OS error in that
reader. The narrow fix passed 110 focused/integration tests, was reconciled
against the installed file and deployed with an exact-hash checkpoint. Aster
health and the six-service sanitized report passed postchecks. This is reader
hardening only; it is not a Codex diagnostic or a new permission.
The completed Home Assistant advisor's saved report had become stale even
though cron continued to invoke its producer. The [freshness recovery](evidence/HA-report-freshness-recovery-2026-10-11.md)
pins a cron-PATH failure, a one-line absolute `qm` path repair, fresh delivery
and reader hardening. This repairs the local report-backed status path; it does
not add Home Assistant control authority or release Codex routing.
An offline Doctor check now detects a missing or over-15-minute HA report file,
and the Aster health wording no longer claims the old Vulkan backend or
unmeasured GPU offload. This script edit is local only until repository
synchronization and operator adoption; it is not an always-on alert.
The [Forgejo/NetBox report reader boundary](evidence/source-report-reader-boundary-2026-10-11.md)
received the same narrow file and malformed-field hardening after a 124-test
local pass. Both existing source reports and Aster health passed postchecks;
no producer, source service or Codex authority changed.

An [offline D3 view candidate](evidence/D3-manual-uncertain-result-2026-10-10.md)
now checks the recorded request after an uncertain native bridge result and
offers only the existing recovery/reconciliation path where the journal proves
one. It is not installed and does not change the limited-release HOLD.
The [recorded-job status candidate](evidence/D3-job-state-presentation-2026-10-10.md)
also distinguishes waiting, offered, accepted, last-reported-running and
uncertain work in the disabled remote-worker view. It is presentation only;
quota classification and routine job handling remain open.
The [terminal-failure acknowledgement candidate](evidence/D3-terminal-failure-ack-2026-10-10.md)
lets a verified failed/stopped native turn be acknowledged before a new
reviewed question, while uncertain turns remain blocked. It is offline only.
The later [failure-category candidate](evidence/D3-durable-failure-category-2026-10-11.md)
retains only an allowlisted code with a confirmed failed turn so the native
view can distinguish limits and outages after a restart. It is bundled in
historical v16, but real provider-code behavior and the current-build release
gate are unproven.

### What the next connected-tool gate actually lacks

**Current reconciliation, October 25:** the paragraphs below preserve the
historical M1 gaps and rejected shapes. They are superseded for the synthetic
authority boundary by the permanent independent ingress, exact Aster WebAuthn
mapping and the passing
[Red/management ceremony](evidence/M1-red-management-ceremony-result-2026-10-25.md).
The missing work is now capability-specific: choose one useful fixed read-only
diagnostic, register a distinct least-privilege caller and projection, and
prove its value and recovery before release. The completed synthetic ceremony
does not itself authorize that registration or deployment.

The first [fixed Doctor capability candidate](evidence/M1-D4-fixed-doctor-capability-candidate-2026-10-25.md)
now narrows that shape to the registered `aster.agent_inference` status only.
Its exact empty request and text-free response contract pass 25/25 combined
tests and reject unsafe, stale or ambiguous evidence as unavailable. It remains
source-only: no dedicated caller, broker capability, gateway, production
schema-2 sidecar, model egress or grant has been created.

The follow-on [single-run producer candidate](evidence/M1-D4-single-run-doctor-producer-candidate-2026-10-25.md)
removes the production evidence gap in source without running Doctor twice.
One fresh invocation supplies the existing operator report, a private local
transcript and the digest-bound fixed-check sidecar; the 23/23 combined suite
proves exact-byte binding, atomic writes, privacy separation and safe abstention
during a mixed update. This is still source-only. The 08:15 schedule and LXC104
files are unchanged, and no caller, broker registration, grant or model route
exists yet.

The subsequent [fixed caller boundary](evidence/M1-D4-fixed-doctor-caller-boundary-2026-10-25.md)
now defines those missing identities in source. A dedicated observer UID gets
one Green `diagnostic.aster-inference.latest` grant through an exact caller
socket; a separate broker-private gateway reads the digest-bound pair and
returns only the fixed projection. The 73/73 combined suite proves enrollment,
revocation, kernel peer checks, absence of approval-group membership and
content-free denial. It is not installed or registered, and Aster still has no
model-visible route to it.

The [frozen deployment bundle](evidence/M1-D4-fixed-doctor-frozen-bundle-2026-10-25.md)
now pins the 12-file Mac/LXC104 target shape, exact four-file rollback set,
eight absent additions, modes, ownership and disabled-staging exclusions. Its
validator passes 6/6, three installed dependencies are hash-pinned and the
measured live predecessors match. An isolated root-only LXC104 staging run
passed Python 3.13 compilation/import and both systemd unit checks, then removed
all temporary files. No final path was modified and no identity, service,
grant, restart, live read or model route is activated. The existing 08:15
report LaunchAgent's recorded last exit is 1 due
to a Mail AppleEvent timeout; disabled staging is independent, while the first
live producer validation must distinguish that pre-existing alert fault from
producer behavior.
The follow-on [inactive additive install card](evidence/M1-D4-fixed-doctor-inactive-additive-install-card-2026-10-25.md)
includes only the eight absent
LXC104 files plus dedicated sysusers identities and leaves both services
disabled/inactive. Broker/Mac replacements, restart, enrollment, grant, read,
route, model call and F2/F6 effects are explicitly excluded. It is prepared but
its first run failed on the absent `/etc/sysusers.d` directory and rolled back
completely before identity creation. The corrected card uses the measured
systemd 257 path `/usr/lib/sysusers.d`; exact target paths are now validator-
enforced. The [corrected retry passed](evidence/M1-D4-fixed-doctor-inactive-additive-install-result-2026-10-25.md):
all eight files are exact, UID/GID 978 and client GID 979 were created, both
units remain disabled/inactive, sockets are absent, production is healthy and
the broker has zero fixed-Doctor rows. No replacement, restart, enrollment,
grant, read, route or model call occurred.

The next producer gate is now frozen in the
[two-file cutover and bounded-canary card](evidence/M1-D4-fixed-doctor-producer-cutover-card-2026-10-25.md).
Its machine validator passes 4/4, the focused producer suite passes 7/7 and a
live read-only preflight matches both predecessor hashes and the unchanged
08:15 LaunchAgent. The canary deliberately invokes only the builder, not the
full scheduled wrapper, so the existing Mail-alert timeout cannot be mistaken
for a producer failure. Mac replacement, one Doctor invocation and publication
of the report pair still require the exact live change decision; caller and
gateway activation, broker replacement, enrollment and any model route remain
later gates.

The [first producer cutover and canary](evidence/M1-D4-fixed-doctor-producer-cutover-result-2026-10-25.md)
passed publication, digest binding, custody, cleanup and recovery checks, but
the fixed state safely abstained because the live Mac Doctor predates the
structured emitter and still probes the retired Vulkan description. The
[one-file correction card](evidence/M1-D4-fixed-doctor-emitter-correction-card-2026-10-25.md)
now generates an exact candidate from the measured live predecessor, adds only
the private-FD emitter and replaces only `check_aster` with the current
service/`xe` contract. Its generator tests pass 3/3, the combined boundary
suite passes 40/40 and `bash -n` passes. The correction and one new canary need
their own exact live decision; no service, grant or model route is active.

Jason approved that exact correction and re-canary. The
[live result](evidence/M1-D4-fixed-doctor-emitter-correction-result-2026-10-25.md)
passes: the production Doctor has the exact generated hash, the same-run fixed
state is `pass`, local and LXC104 report bytes are digest/timestamp bound, both
remote staging paths are absent and the fixed services remain inert. The
overall Doctor still reports two unrelated operational failures; they do not
alter the typed inference result. The producer/evidence gate is complete.

The first broker replacement candidate was then rejected before deployment:
its two source files predated live Forgejo project-document support and would
have removed that capability, dedicated socket and batch-write route. The
[reconciled replacement card](evidence/M1-D4-fixed-doctor-broker-reconciliation-card-2026-10-25.md)
now starts from the exact deployed sources, preserves those newer routes and
adds the fixed Doctor path. Its exact-source generator reproduces both
candidate hashes, local compilation passes and 51 focused tests cover both
feature families. The first approved replacement attempt rolled back: its
postcheck used the non-client `aster` identity, and rollback then exposed an
incorrect SQLite ownership restore. Production is recovered at both original
source hashes, healthy broker/Aster services and an `ok` database integrity
check. The corrected retry uses registered client `hlabagent` and restores the
database as `hlabroker:hlabroker` mode `0600`. The first corrected retry then
failed closed on a measured startup-readiness race: active state plus socket
existence preceded an accepting listener. Rollback recovered production. The
final pinned script requires a bounded successful `hlabagent` health-probe loop
before postchecks and uses the same loop during rollback. Jason approved the
final retry and the [live broker result](evidence/M1-D4-fixed-doctor-broker-reconciliation-result-2026-10-25.md)
passes: both reconciled source hashes are live, registered-client health and
database integrity pass, Forgejo project-document routing is preserved, fixed
rows remain zero and the fixed services remain inactive. The separately
approved [activation result](evidence/M1-D4-fixed-doctor-activation-result-2026-10-25.md)
then passed after one pre-effect escaping correction: UID 978 is the sole fixed
observer, one Green non-probationary grant exists, both dedicated units are
active/enabled with zero restarts, and exactly one typed fixed request is
consumed. Broker/Aster health, SQLite integrity and the Forgejo project-document
route remain intact; the root-only rollback checkpoint is retained. The next
gate is a preregistered usefulness evaluation through this fixed path, with any
model route and broader authority still separate.

That evaluation now has a
[frozen synthetic fixture and blind-review scorer](evidence/M1-D4-fixed-doctor-usefulness-preregistration-2026-10-25.md).
Eight balanced cases cover `ok`, `warn`, `fail` and `unavailable`; acceptance
requires at least 7/8 complete four-dimension passes and zero unsafe claims.
Its private capture, candidate-blind packet builder and packet-bound scorer
stop on first failure and prevent incomplete answers or mismatched packets from
passing. A proposed tool-free accepted-9B profile now pins the local endpoint,
engine and every evidence component with one attempt, 60-second per-case and
600-second outer bounds; 22 focused boundary tests pass. The packet explicitly
grants no authority or routing promotion, and no model request or live Doctor
read has occurred. A durable attempt journal and effectful live card remain to
be frozen before an evaluation.

The immediate [post-authority candidate-G preflight](evidence/D4-candidate-G-post-authority-static-preflight-2026-10-25.md)
is STATIC GO: its dry-run digest and all eleven source identities still match,
the owner-only packet remains exact, and no key, lease or model request was
used. This preserves the already-approved, unspent tool-free evaluation while
the same-cycle F2–F5 and executable F6 recovery gates remain closed.

Repository evidence shows [M1 Stage1](evidence/M1-stage1-deployment.md)
deployed caller binding and restrictive checks, while the
[Stage2 approver/assurance candidate](evidence/M1-stage2-candidate.md) is **not
deployment-ready**: the current Authentik claim has not been proven to convey
passkey-specific assurance to Companion, and the allowed Aster process can
still supply actor metadata at the approval socket. This is an authority
boundary, not a model-quality problem. Do not solve it by giving Codex SSH,
root, a generic broker token or a broad Keychain exception.
The Aster-as-approver Stage2 candidate is retained for provenance but
superseded as a deployment shape by the separate-verifier proposal.
The [approval-ingress options](evidence/M1-approval-ingress-options-2026-10-10.md)
record a dedicated verifier as the preferred candidate if in-app privileged
approval remains required. A [read-only live recheck](evidence/M1-live-approval-boundary-recheck-2026-10-11.md)
confirmed Aster's approval-socket group membership and a deployed broker
source difference from the repository candidate. The verifier is not deployed,
and the passkey-claim proof is still missing. A [synthetic independent-ingress
candidate](evidence/M1-independent-approval-ingress-candidate-2026-10-11.md)
passes local denial tests and a disposable HTTP-to-broker socket check, but has
no production process or network authority yet. This check did not prove the
real passkey claim or remove Aster's socket access.
An uninstalled process factory now fails closed on missing/mismatched identity
configuration and deliberately has no passkey-promotion setting. The focused
suite passes 23 tests. Separate UID, socket directory, private listener and
proxy-route proofs still gate any deployment.
Retained aggregate proxy logs do not establish routine Yellow approval use;
the separate-ingress **production rollout is deferred** on value/overhead
grounds while Stage2 and connected tools stay held. Keep the offline candidate
for a concrete later need rather than creating a new service by default.
The [Green-only admission assessment](evidence/M1-Green-only-admission-assessment-2026-10-11.md)
finds a possible narrower route to one fixed read-only diagnostic, but the
existing `hlabagent` has broader live capabilities and cannot be reused for
Codex. A distinct least-privilege worker and an explicit M1 gate amendment
would be required; neither is authorized or deployed.
The [live aggregate value check](evidence/D4-live-aggregate-value-check-2026-10-11.md)
found a fresh saved Doctor observation of `fail` across 32 checks but no
failing-check identity. That fails the minimum usefulness threshold for an
aggregate-only Codex diagnostic. Do not create a Green worker or grant merely
for that aggregate; require a privacy-reviewed, named diagnostic output and
held-out value evidence before revisiting the M1 gate.
An [approval-socket lifecycle check](evidence/M1-approval-socket-lifecycle-2026-10-10.md)
also found that a main-broker restart had removed the independent approval
listener's pathname while the service still reported active. The listener was
restored, and a one-line systemd fix was deployed and verified across one
normal main-broker restart. It does not prove full-stop independence or satisfy
the Stage2 identity/assurance gate.

The existing [`sysadmin_investigation.py`](../../../services/aster-agent/sysadmin_investigation.py)
and [`doctor_incident_adapter.py`](../../../services/aster-agent/doctor_incident_adapter.py)
are useful **offline** building blocks: registered evidence types, bounded
incident state and a fixed-path, aggregate Doctor observation. They are not a
connected Codex tool. The Doctor adapter currently supplies status, check
count and report digest, not enough per-check evidence to diagnose a real
fault. The generic observation contract permits free-text summary/fact values,
so source-local sanitization and an explicit data projection remain necessary
before any model egress. The smallest next implementation is a fixed-target,
read-only evidence projection and denial tests, reviewed against M1 before
connection; it is not another framework or a live sysadmin pilot.
The offline [incident display boundary](evidence/D4-next-step-presentation-boundary-2026-10-16.md)
now constructs proposed next steps from registered fields instead of copying
persisted extra fields into UI frames. This closes a presentation leak in the
candidate only; it does not sanitize producer facts for a model or authorize
a connected tool.
The [offline Doctor model-egress projection](evidence/D4-Doctor-model-egress-projection-2026-10-16.md)
now builds a minimal typed status view for the two registered Doctor producers
without copying their summaries or arbitrary facts. It is source-only, cannot
authenticate a producer by itself, and does not change the M1 or usefulness
gates for a connected tool.
An [offline malformed-producer check](evidence/D4-sysadmin-evidence-type-boundary-2026-10-15.md)
now makes wrong field types, boolean schema versions and non-finite fact values
fail with a controlled contract error; it changes no live authority.
The [October 17 persisted-record check](evidence/D4-incident-restore-boundary-2026-10-17.md)
also rejects damaged observation plans/rows and naive clocks with controlled
errors. The normal restore path and 30 focused tests pass. This is source-only
and does not authenticate a producer or authorize a connected tool.
The [Doctor projection gate](evidence/D4-Doctor-structured-evidence-gate-2026-10-10.md)
specifies why free-text parsing is insufficient and how one producer-owned
check ID can be tested offline before any model sees diagnostic evidence.
The [typed-check fixture preflight](evidence/D4-Doctor-structured-fixture-result-2026-10-10.md)
now passes locally, including fail-closed pairing and private-text exclusion.
It is not deployed or connected. Review of the deployed Aster health tool
found a broader existing baseline: it already supplies Doctor's bounded
free-text summaries to Aster's model context. The typed candidate therefore
needs to show a useful privacy/specificity tradeoff against **that** path, not
just against the aggregate-only adapter. Blinded usefulness, M1 authority and
real-incident gates remain open. Do not promote schema 2 or expand model egress
on the strength of the parser tests.
The [seven-case offline contract comparison](evidence/D4-Doctor-structured-fixture-result-2026-10-10.md)
found no family-identification gain over today's human-summary path for its
single Aster failure. It did demonstrate that the current Aster reader forwards
dynamic text and does not reject a stale report. The next low-complexity
candidate was to harden that existing reader and keep aggregate status for
simple questions; schema 2 remains unpromoted. On 2026-10-11, the candidate
was tested against a copy of the deployed gateway, including required imports.
All 199 gateway tests passed. The narrow reader change was deployed with a
retained source checkpoint; Aster stayed healthy and its service account could
still read the current 32-check report. This changes the existing local
health path only. The D4 connected-tool, schema 2, blinded usefulness and M1
authority gates remain open.
The twelve reviewed incident descriptions now also have a separate
[offline extension draft](evidence/D4-development-corpus-extension-draft-2026-10-19.md)
for repair scope, postcheck and latency fields.  A subsequent
[qualification-boundary check](evidence/D4-development-corpus-qualification-boundary-2026-10-19.md)
allows that draft to be schema-tested but rejects it as qualification evidence
until it has complete status, Jason review for every case and no unreviewed
provenance marker.  This prevents AI-authored extensions from silently
becoming promotion evidence; it does not complete D4 or M1.
The subsequent
[qualification-gated plan builder](evidence/D4-qualification-gated-evaluation-plan-2026-10-20.md)
refuses that unreviewed extension and the incomplete canonical intake before
any evaluation can be planned. An eligible input produces only a digest and
bounded counts with model, tool and execution authority explicitly false.
Its focused offline suite passed 16/16 tests, including malformed container,
target and review-field types. This prepares a reproducible D4
evaluation boundary without reviewing the draft on Jason's behalf, calling a
model, granting a tool or creating promotion evidence.
The existing offline fair scorer now also has a
[malformed-input boundary](evidence/D4-fair-scorer-malformed-input-boundary-2026-10-20.md):
case, capability, key and review collections fail closed on unexpected shapes
instead of crashing or being interpreted as missing review. The combined
focused D4 suite passed 28/28 tests. This hardens future comparison only; no
corpus has been reviewed and no model has been evaluated or promoted.
The synthetic investigation runner now also has a
[fixture and transport boundary](evidence/D4-investigation-fixture-and-transport-boundary-2026-10-21.md):
it validates the complete private evidence catalogue before a transport call,
rejects malformed response containers and retains only bounded typed metadata.
The complete eval unit suite passed 110/110. This protects future evidence
capture; it does not call or qualify a model, connect a tool or advance M1.
The lower-level engine now also enforces the package's closed
[freshness vocabulary](evidence/D4-investigation-freshness-vocabulary-boundary-2026-10-22.md)
before transport and applies the same 16,000-byte development-case envelope.
Unrecognised freshness and oversized observations cannot reach the model, and
the complete eval suite passes 112/112. This aligns two offline validation
layers; producer authentication, representative incidents and connected-tool
authority remain open.
The fresh package now also enforces a
[bounded engine-result journal boundary](evidence/D4-engine-result-journal-boundary-2026-10-22.md):
unexpected raw fields and oversized results are rejected before journalling,
and the surviving started marker makes the uncertain attempt non-replayable.
The complete eval suite passes 113/113. This prevents a faulty injected engine
from persisting private reasoning; it does not establish investigation quality
or connected-tool authority.
The same boundary now also rejects
[non-finite engine values](evidence/D4-engine-result-finite-json-boundary-2026-10-22.md)
before a finished event is journalled. A synthetic `NaN` result did not reach
the journal, the surviving started marker blocked replay, and the complete
eval suite passed 114/114. This makes the evidence portable JSON; it does not
turn development results into qualification or promotion evidence.
The private journal now also has a
[four-MiB existing-file boundary](evidence/D4-ledger-size-boundary-2026-10-22.md)
checked on the locked descriptor before reading. An owner-only oversized
fixture was rejected before parsing, and the complete eval suite passed
115/115. This limits corrupted-input resource use; it does not reconcile or
rewrite an existing journal.
Resume now also
[revalidates exact journal rows, events and finished results](evidence/D4-journal-resume-validation-boundary-2026-10-22.md)
after verifying the chain. Correctly rehashed fixtures with an unexpected
outer field or a private-reasoning result were rejected, and the complete
eval suite passed 117/117. This closes a malformed-record acceptance path; the
hash chain remains an integrity structure rather than a signature.
The fresh executor now also enforces a
[one-MiB local-service response boundary](evidence/D4-local-service-response-size-boundary-2026-10-23.md)
before decoding health, metrics or completion JSON. An oversized fixture was
rejected and the complete eval suite passed 118/118. This bounds future runner
memory use; it does not call or qualify a model.
The executor now applies the same
[one-MiB boundary to its case bundle and release manifest](evidence/D4-evaluation-input-envelope-boundary-2026-10-23.md)
before JSON decoding and rejects repeated object keys. Normal, oversized and
duplicate-key fixtures behaved as expected, and the complete eval suite passed
119/119. This closes a local-input ambiguity and resource boundary; it does not
read the private holdout, execute the evaluation or advance D4/M1.
The executor also now
[ignores environment-derived HTTP proxies](evidence/D4-local-credential-proxy-boundary-2026-10-23.md)
for its fixed private inference endpoint while retaining redirect denial. A
synthetic proxy setting was excluded and the complete eval suite passed
120/120. This prevents an invoking-shell proxy from becoming an unintended
credential or payload path; it does not read a key, make a request or authorize
the future run.
Health and completion response JSON now also
[rejects repeated object keys](evidence/D4-local-service-duplicate-key-boundary-2026-10-23.md)
instead of retaining the last value. Normal and ambiguous synthetic responses
behaved as expected and the complete eval suite remained 120/120. This closes
an offline parser ambiguity without making a model call or advancing D4/M1.
The shared bounded decoder now also
[rejects non-standard non-finite numeric tokens](evidence/D4-strict-json-number-boundary-2026-10-23.md)
across case, manifest, health and completion data. Normal input passed while
`NaN` and both infinities were rejected; the complete eval suite remained
120/120. This preserves portable JSON semantics without executing a run or
changing authority.
The private journal now also enforces the investigation engine's
[closed terminal-status vocabulary](evidence/D4-engine-status-vocabulary-boundary-2026-10-23.md).
Invented, malformed and oversized transport-error statuses were rejected before
a finished event, and the complete eval suite passed 121/121. This prevents a
faulty injected engine from turning an unknown status into a completed session;
it does not execute or qualify the holdout.
Journal resume now also uses a
[strict JSON decoder](evidence/D4-private-journal-strict-json-boundary-2026-10-24.md)
that rejects repeated object keys and non-standard `NaN`/infinity constants
before the existing shape, sequence and hash-chain checks. Synthetic ambiguous
rows were rejected and the complete eval suite passed 122/122. This closes an
offline private-record parser ambiguity; it does not read the holdout, call a
model or advance D4/M1.
The future local runner's readiness check now also enforces a
[single finite, nonnegative requests-processing gauge](evidence/D4-local-idle-metric-boundary-2026-10-24.md).
Missing, duplicate, negative, nonnumeric and nonfinite synthetic metrics were
rejected; the normal labelled zero gauge passed, and the complete eval suite
passed 123/123. This closes an offline idle-admission ambiguity without calling
the service or authorizing the holdout run.
The private journal admission layer now also enforces a
[nested engine-result schema](evidence/D4-engine-result-nested-schema-boundary-2026-10-24.md)
for steps, metadata, sanitized answers, checks, observations, timing, attempts
and failure records. Synthetic nested reasoning and malformed/nonfinite nested
values were rejected before a finished event, while the complete eval suite
passed 124/124. This protects future private evidence without executing or
qualifying a model.
The same admission layer now also binds
[terminal status to the retained final answer](evidence/D4-terminal-answer-lineage-boundary-2026-10-24.md)
and binds non-transport attempt counts to retained steps. Contradictory or empty
terminal results fail before journalling, and the complete eval suite passes
126/126. This protects later scoring and audit; it does not read or qualify the
holdout, call a model or connect a tool.
The journal and producer now additionally enforce a
[terminal/failure lineage boundary](evidence/D4-terminal-failure-lineage-boundary-2026-10-24.md):
rejected terminal answers are discarded, nonterminal statuses cannot retain a
terminal answer, failure metadata must agree with transport status, and transport
attempt counts include exactly the failed call. The complete evaluation suite
passes 128/128. This is evidence hardening only; D4 qualification remains open.

## Immediate next action and stop rule

Do not spend another cloud question on the deferred manual-Codex button. M1's
synthetic authority proof is complete; its next work is a separately designed
fixed read-only capability, not broader broker access. D4 candidate-G remains
exact and unspent but is superseded as the proposed workload by the separately
installed, inactive candidate-H. Candidate-H's dedicated UID/GID 977
descriptor bridge passed target-Linux custody and fictional-credential
validation with zero model calls and credential reads. Its live execution is
blocked on the October 26 F2 runtime result, subsequent F3/F4/F5 evidence and a
corrected executable F6 effect transaction. The
[exact admission-binding proposal](evidence/Stream-A-candidate-H-F4-F5-admission-binding-proposal-2026-10-25.md)
freezes the missing composite artifact, controller field, durable-state
binding, candidate-H invocation and recovery proof. The platform owner has now
supplied that source implementation and its tests; the four-file inactive
install passed 69/69 target tests and an isolated real-wrapper regression.
M3's absolute interpreter, root execution identity and key-file custody are
pinned; the live card must recheck them for drift. Do not activate F6, stop
consumers, call a model, create a receipt or infer success from the scheduled
F2 timers.

The source-only [candidate-H credential correction](evidence/D4-candidate-H-descriptor-credential-boundary-2026-10-25.md)
replaces environment-key access with a bounded inherited descriptor and passes
the complete 168-test evaluation suite. It is a new, unauthorized digest; its
inactive target custody is installed and validated, but it has not run. The
actual descriptor opener is pinned and installed inactive; candidate-G's
approval does not transfer.
Stream A rejected its initial
[root-child descriptor launcher](evidence/D4-candidate-H-descriptor-launcher-proposal-2026-10-25.md):
the child could reopen the protected file despite environment exclusion. The
[dedicated-identity correction](evidence/D4-candidate-H-unprivileged-execution-correction-2026-10-25.md)
uses fixed UID/GID 977 with no supplementary groups, separates immutable inputs
from private outputs, and passes nine focused tests plus the complete 168-test
suite. Its first inactive install rolled back on an extensionless-loader defect;
the corrected second attempt passed the target-Linux negative custody and
fictional-descriptor probes with zero credential reads and zero model calls.
The unit remains static and inactive. A live run still requires fresh
F2/F3/F4/F5 evidence, executable F6 recovery, an exact run card and a separate
model-call approval.

The [F3-from-F2 converter](evidence/F3-from-F2-inactive-install-result-2026-10-25.md)
is now installed inactive at its reviewed hash and passed 27/27 target-Linux
tests. It can derive the durable F3 receipt from an unchanged, complete F2
terminal result without repeating the archive scan. Receipt production remains
a separate effect approval after F2 reconciliation; failed or uncertain F2
evidence writes nothing.

Future F4/F5 authentication now uses the
[installed negative-control metadata probe](evidence/F4-F5-metadata-auth-inactive-upgrade-result-2026-10-25.md):
no authorization and a fixed invalid bearer must both return `401` before the
real key can return `200` with the exact model. This removes the former hidden
one-token completion from the no-model-call evidence path. F4/F5 remain
unproduced. The downstream F6 helper pin is now
[installed and validated inactive](evidence/F6-exercise-auth-pin-inactive-upgrade-result-2026-10-25.md):
the complete target suite passed 94/94, inert invocation remained disabled and
no lease or service effect occurred. F6 arming still requires fresh F3–F5
evidence, a corrected exact live card and separate approval.

The static candidate-H/M3 F6 card now passes independent review, and the
[pure live-plan layer](evidence/Stream-A-candidate-H-F6-pure-plan-review-2026-10-25.md)
freezes exact payload schemas, identities, commands, paths and bounds without
effects. It is deliberately not an admission gate: the later orchestrator must
submit each phase through the durable adapter so M3 cannot precede an accepted
candidate-H outcome. The source-only sequence and fixed intent/effect driver
now enforce that order and retain separate D4/M3 start/outcome records. The
[composition review](evidence/Stream-A-evaluation-composition-source-review-2026-10-25.md)
found and corrected a pre-install guest dependency gap: both guests lack the
host-only lease module that the original verifier imported. Platform commit
`37452660` is dependency-closed, passes 95/95 locally and on Proxmox, and its
two-file packet returns the exact disabled result in both target guests with
an empty `PYTHONPATH`. Nothing was installed during that proof. The revised
13-path inactive card is recorded at platform commit `8e6ed141` and needs a
fresh exact installation approval because one pinned hash changed.
That approved attempt then exposed a separate host import-root omission and
rolled back completely; production and the October 26 F2 timers remained
healthy. Platform V3 at `4d682e6f` pins both installed module roots, removes
the last guest-only host import, passes 96/96 target-Linux tests and completes
a temporary target import. Its subsequent
[inactive installation](evidence/Stream-A-evaluation-composition-inactive-install-v3-2026-10-25.md)
passed all 96 target tests, installed the exact 13 paths, imported through the
two fixed module roots and returned the exact inert result in both guests. F6
remains disabled and state-free. Fresh F3-F5 evidence, the activation/recovery
card and live-effect approval remain open; the two consumed packets must not be
retried.
The immediate [post-V3 activation-card reconciliation](evidence/Stream-A-F6-post-V3-activation-card-reconciliation-2026-10-25.md)
then found that the candidate-H card still pins the pre-V3 restore observer and
omits the twelve other installed V3 paths. It is therefore NO-GO as live
authority. The platform owner must issue one current-packet card before F6 can
be considered for arming; the installed code remains inert and accepted.
The
[owner-before-heartbeat unit correction](evidence/Stream-A-F6-owner-heartbeat-ordering-inactive-install-2026-10-25.md)
is installed inactive with a root-only rollback checkpoint, 4/4 focused tests
and unchanged October 26 F2 timers. The next offline F6 work is to implement
and prove the injected arm, workload-verification, recovery and cleanup
handlers; no live arming or model call follows from the inactive correction.
