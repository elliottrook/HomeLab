# November 5 R2 failure, assisted restoration and distinct R3 continuation

R2 did not qualify. Production was restored and released at15:18:12 Vancouver
UTC−07, before its15:45 deadline. Jason's operational Stream A continuation
remains authorized; this is not a preparation-only heartbeat. R1 and R2 are
spent failed qualifications and must never be replayed or counted as passes.

## R2 actual outcome

The owner and independent guardian both reached RESTORATION_INCOMPLETE. A
captured-inactive/static News ingest worker remained failed after a controlled
SIGTERM: Result=signal, ExecMainCode=2, ExecMainStatus=15, zero PID/tasks.
The owner was allowed its reserved restoration window; neither it nor a live
restoring guardian was interrupted. After both scopes were empty, the exact
binding and session lock admitted a separately launched assisted recovery.
It retained manual-assistance/trial-failed evidence, restored the captured
inactive state, verified all original entry/checkpoint identities, used the
reviewed no-catch-up Paperless policy, verified production and released.

The final session is released, production_restored=true, deadline_missed=false,
manual_assistance_required=true, trial_failed=true. The authoritative ledger is
failed / FAILED_RESTORED at1793917092. The assisted recovery terminal explicitly
says qualification_passed=false and application_job_success_claimed=false.
At1793917850 all lease/drain/operation markers were absent. The accepted
production health probe inside recovery is not a candidate benchmark.

| Protected path under /var/lib/local-ai-lab | SHA-256 |
|---|---|
| exclusive-sessions/b60-exclusive-20261105-day-r2/session.json | 0f6d9ba292d93b90fcf7b535b20880504b91d632b49f373e2101ba3a60983a82 |
| exclusive-sessions/b60-exclusive-20261105-day-r2/entry.json | c3b23ff7605b31992afcc388f26330bad8df4dadd8dea6ed41cce0b1cd6d86b4 |
| exclusive-sessions/b60-exclusive-20261105-day-r2/admission.json | 1541cbd95520dc475079576fe3e936a8dd12d956eb76b3e82282e2a11c3103f0 |
| exclusive-sessions/b60-exclusive-20261105-day-r2/manual-recovery-terminal.json | 65d6683c9335a2ab800b20e2a0aa49cf13523322d722f553395ab36002044364 |
| exclusive-releases/b60-exclusive-20261105-day-r2.json | 66397cdb0f07c601d8645073f145a2066607b6629d1677a175404ed68dcacb22 |
| reservations/records/b60-exclusive-20261105-day-r2.json | b8b8723617361a73a869af684b49cf837e69589e0721928159e064566ae5b726 |

Executed assisted source remains root-private at
/root/b60-timer-recovery-operational-20261105-v3/assisted-R2-42e7b7d7.py,
SHA25642e7b7d7b397f672d755e66e95d168f2a913357b87404b9e2d168d42c7d4a8ef.
The exact historical source accompanies this record; it is guarded to the spent
R2 state and must not be replayed.

## Reviewed permanent correction

Source commits5cad10576098fec46672a7b39918d66538b41a75 and
14224398a7a604207153e317ee62e6622e47906d, final tree
0ac22616136f6738c8c839b0a10e9c11da9f6cb3, add the narrow state correction.
Only a captured-inactive static service, quiescent with exactly the controlled
SIGTERM tuple, may have its failed state reset. OOM, exit-code, other signals,
unknown fields, nonzero PID/tasks and unsupported state remain refused. No job
is restarted. Durable intent is written before reset; observed-inactive follows
verification. Interrupted-job evidence is retained, never reported as success.

The completed-integrity scheduler creates only a new date-specific qualification
clock, requires an actual complete no-stack-effect integrity terminal bound to
current archive identity, and checks freshness now and through the claim time.
Actual admission independently repeats freshness/identity checks. No fabricated
future scan or runtime result is accepted. The clock is nonpersistent, with no
missed-event replay and no duplicate preparation during another owner's lease.

225 controller tests, eight scheduler tests and115 B60 tests passed against the
explicit source checkout. Target Linux passed15 unit-adapter and two completed-
integrity clock tests using pinned runtime and tool roots. These are synthetic
checks, not live qualification. Portable source patches accompany this record.

Final staged candidate map:
e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2.
Bundle descriptor1bee3bd051124641a4a8f801ee372688324cd98695dccf8ae9259a56b38ed548.
Root-private packet /root/b60-inactive-state-operational-20261105-v2/packet.tar,
SHA2569bc54094169fa3f9b48494b3f554ed6081e6595cec18ccf52755f4a15f52c91e;
45-tool manifest1a13506f01bf60c9827f6667d12aa3f77955f1b9765b68514bb32b93c6c62979.
Earlier v1 is retained staged history, never installed or armed.

## Distinct R3 capacity and next gate

R3 b60-exclusive-20261105-day-r3 is actually reserved17:15–18:00 with recovery
reserve through18:15, created1793917386. An initial16:30 proposal was refused
before any reservation write because the TTS owner has16:00–17:00 plus its
restoration buffer through17:15. That booking is preserved. No overlapping run
or early use is permitted. An early read-only archive scan began before TTS,
under common exclusion with deadline15:50. A complete receipt, source migration,
five fresh plans/profile and independent clock verification are required before
calling R3 armed. Completion and exact receipts are recorded below when observed.

No 27B+ candidate experiment or model change is scheduled here. Restore-only
success would still leave independent owner-loss/resource qualification and the
expanded reasoning-on grounded capability/complete-answer p50/p95 gates open.

## Early integrity and disposable systemd evidence

The bounded read-only R3 integrity service completed at1793918126
(15:35:26), before TTS, with no AI-stack effects. Terminal SHA256
1e258ae5c62cb8022e5ec4a6b0edaf8c7b9207a1bddd5850ee40d8a378675fb1;
archive proof retained-archive-integrity-sha256:
2606b6aa503268bf4d01acc240290455d921b72e5fbd83a825831480dc51888a.
The independent service was inactive/success on observation1793918166.
The exact early preparation source SHA256 is
29b0ee4d9cce8df769d3bd997ae34490c8e483f631f01b2da73890e511567752.

A disposable systemd oneshot running only sleep first failed a test assertion
that the historical start timestamp remained unchanged. Linux reset-failed
clears that metadata; cleanup ran and no production service was involved.
The corrected test allows cleared history, requires zero PID and an adapter
command trace containing no start, and passed at1793918217. It reset only the
disposable unit, then removed it. No production job or model was executed.
Both test revisions remain source history; revision2 source SHA256
c578b053d4a05242025e4a95c80464a7b6d97c68d73557dbf6c024f887d42603.

## Actual final R3 installation and arming

Final source map e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2
is installed, with imports and exact bytes verified. All five declared guests
have unit helper f4781de620e9c0c10bf01eab162eb2564d8baf1d4d84670117649d368325bcbd.
Each source-local helper checkpoint manifest is
aa6701595afacb9a594f245b622dbc9400f6f13df9bff00098a7cbb4bfbb7f78.
The host source checkpoint manifest is
990aa117433f9e6510fea8cd7837a3a62e2f8f68fc3d8bda6077b2043904c132;
journal update SHA25689bb64638cc69d336276bb36c6a1504d6691cfb1d83dc13f2f1be0ed2f9b57b5,
plan SHA2562cba957bd6436e99efb33f22ed9f9b91f782264551720ca1ebf6baf738b274ed.
All migration phases held shared exclusion and idle/ready guards. No production
service was stopped, no stack transaction or model experiment was run by the
migration, and no backup, driver, package, mount or credential changed.

Five fresh metadata plans and the protected qualification-only, experiment-null
profile were prepared. The new clock was then actually armed. Independent
observation1793918346 proves enabled/active/waiting timer, next
2026-11-05 17:15:00 America/Vancouver (host MST, UTC−07), empty LastTriggerUSec;
its service is inactive, PID0, with empty start timestamp. No R3 preparation
timer exists. All30 runtime pins, five plans and four helper hashes per guest
match the actual protected profile. Arming is not a qualification pass.

- Arming receipt /var/lib/local-ai-lab/arming-receipts/b60-exclusive-20261105-day-r3.json:
  a1b5addd5ec22ee472e3d56b0a59d6886092d0fd644d1f49c46f16a062b1db95.
- Profile SHA256 d544c878259cec16863459c995616f6aca1b9ca96658f2826e2266af1c933139.
- Booking SHA256 6e0294b645230d1e16d39f428834ac91571efc113eaf7d992bf36e2da597abba.
- Qualification service SHA256 95bd453416c2bffbe0eaedf17029506a48c88a1d19794a17afc3b4aa69507524.
- Qualification timer SHA256 3b98c60f025c885a169819d7a8810200d5e1f00258ef952e9c7674252df7355b.

At1793918389, all core Agent/llama/Speech/UI/broker units are active/success.
News, Paperless and EPUB monitor timers are enabled/active with future dates
or monotonic intervals; idle workers are inactive/success. The retired EPUB
worker timer remains disabled/inactive. No runtime mask or temporary Paperless
deny gate remains; lease/drain/operation markers are absent. These observed
postchecks do not manufacture application job success. The source update is
terminal installed and unactivated except for the separately reviewed new clock.

The existing operational result follow-up is updated to17:25, carrying exact
R3 identity/source/receipt and restoration-window instructions. Proxmox owns the
actual scheduled transaction independently; the Codex follow-up requires the
computer/app to be available. No running Codex background process is promised.
The stale October31 arming automation stays deleted. Broader programme
automations remain active.

## Peer receipt and owned response

Adaptive's R1 audit was read, including its independent helper's safe session-
lock refusal. Its two requested permanent fixes are installed as documented in
the prior R1/R2 record; no no-op owner is now required. R2 exposed the distinct
controlled-SIGTERM state gap, corrected above. This publication records B60's
receipt and response; pushing it does not prove the peer read it.

| Commit | Path | SHA-256 |
|---|---|---|
| 0233187b2a6afd17aa4fcb4420b530dd04b7a3a3 | docs/projects/AI Projects/evidence/B60-daytime-exclusive-recovery-2026-11-05.md | 9ca4c396354ce296475bac8bcebc327580e1541808f17ad9f9496386111fc3d6 |
| 6fb0207fec5190e0c34ed3bc72ea38e128f06127 | docs/runbooks/Local-AI-Lease.md | 064b56ee8fca8aad37e9ae627cf119c581c3f8d8ad7d9782ccfeb0fa23b31d4c |
| 6fb0207fec5190e0c34ed3bc72ea38e128f06127 | docs/projects/Local-AI-Platform-Split.md | 6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7 |
| 9c6d996d4649a7fb6e228efc67da0f66b3098a4c | docs/projects/B60-Inference-Engineering/daytime-r1-assisted-r2-armed-20261105.md | 0826ea989e793611cac785dc08fbba7e661dc51da8a830a9b06ae8f8fc0f93f4 |
