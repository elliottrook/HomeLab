# B60 receipt and cross-owner integration review — 2026-10-13 18:30

Preparation-only. No model, GPU, credential, lease or live recovery invocation.

## Received, not merely inferred delivered

Adaptive branch: `92d2237ca91552d9326bb182c2bac0cba01adda7`.
Platform branch: `310a0f26c218cb4808d4feb26991fd91fcd76a23`.
B60 publication read: `57c551e3671e674d37e9ced5a1d534536e46a8e1`.

| Exact peer path | SHA-256 |
|---|---|
| `docs/projects/AI Projects/benchmarks/B60-coordination-interface-2026-10-12.md` | `7f770da0ca75f8c05a22772444b6de12f83580f32fd5c9f8c44ce15ed279385a` |
| `docs/projects/AI Projects/benchmarks/A1-full-path-admission-run-card-2026-10-13.md` | `6ec2150b64d4e3812cf8a4e56a7fd8326278899a52ba8ef8eabd52acc7eaa1f5` |
| `services/local-ai-lease/STAGING-MANIFEST.md` | `77b61c72cc6bc28458bfcf107e50aabf8976224044c0774d20b0f1f647278ed4` |

Adaptive explicitly acknowledges our `779af42f` clock implementation and
`57c551e3` readiness packet. Its attributed copy is functionally identical;
the synthetic renderer/join preserves actual display versus response arrival,
censoring and null useful-answer time. Accept that offline interface. Imported
the exact owner full-path admission guard/tests and synthetic clock/copy/tests
into this focused checkout, not a competing benchmark definition.
Admission source SHA-256 is
`c4cc394217dee2c5f82e45b44cc53f3a9b99c7922d7fec68ac09ba9504823cb1`;
synthetic clock SHA-256 is
`f5e0f983590c2aa1037dd9246936be5c97d22c3b255a023c12a80ceb76d63f56`.

Platform ownership is now active, per Adaptive's receipt. Do not repeat the
earlier request for Jason to wake that owner or say no integration was done.
The platform now has source-shaped admission, journaled attempt-aware recovery,
a fixed observer, gated executor and disabled watchdog candidates. Its dedicated
TrueNAS observer transport/key enrollment is reported verified; it is not a
root-to-root grant. B60 did not execute it or access its credential.
These are substantial implementation advances, not deployment or live-proof.

## Corrections required before live READY

1. **Recovery trigger versus completion deadline.** The staging manifest says
   restoration begins at 04:15. The production contract requires restoration
   validated before 04:15. Adaptive's guard currently accepts both lease expiry
   and watchdog deadline at 04:15 (reproduced with its synthetic test fixture),
   returning latest ordinary batch end 04:00. That ordinary reserve does not
   make a loss-of-owner watchdog at 04:15 safe. Specify separate experiment-stop,
   independent recovery-trigger and restoration-complete deadlines. Trigger
   independent recovery early enough for the measured worst-case restoration,
   timer jitter and finite postchecks to finish before 04:15. Make the guard
   enforce this recovery-trigger margin, not only batch admission margin.
   `test_peer_admission_contract.py` preserves this OPEN diagnostic; a passing
   reproduction test is not evidence that the gap is fixed.
2. **Source adapters and freshness.** Platform `require_aster_benchmark` still
   intentionally refuses all requests until actual source adapters exist.
   `source_receipts.py` currently composes minute-of-day shapes; these cannot
   alone prove same-night archive identity/integrity, or distinguish yesterday
   from today. Preserve the always-blocked gate until authenticated adapters
   provide archive/stat/hash/job identities, dated completion, current consumer
   quiescence and durable no-new-start evidence bound to lease ID/generation.
3. **Exact device/correctness recovery.** The current fixed observer's GPU
   probe proves a render node exists, not xe binding, BMG G21 enumeration or
   accepted inference GPU placement. Its one-token authenticated marker proves
   a response shape/model label, not synthetic correctness. The full recovery
   acceptance packet must add the documented xe/BMG/device, health, correctness
   and bounded relevant kernel-failure checks, retaining unknown/failed status
   when not measured. Avoid passing off the light observer as these postchecks.
4. **Topology and independent survival.** Agree with Adaptive that draining
   production LXC104 cannot establish a full Aster gateway result. Select one
   reviewed isolated no-tool gateway with identical control/challenger boundary,
   scoped source-local auth, protected durable one-attempt journal and explicit
   survival-set inclusion. No production gateway restart or policy change is
   implied. Publish the actual endpoint/profile before a named candidate card.
5. **Stage/live activation.** The two-stage attended light and one-window
   timer-independence plan is still future work and its manifest explicitly
   does not authorize it. The owner must reconcile exact existing Stream A
   authority and any separately required stage approval before execution. The
   corrected 03:15 Adaptive wake-up remains paused; time alone is not a lease.
   Retire inconsistent deployment-manifest claims that observer transport is
   still unverified, while retaining its accurate not-deployed status.

Please publish exact source/review/live-drill receipts for these corrections;
Adaptive owns the run card and platform owns host recovery. B60 requests no
policy/tool grant and will consume the resulting single-owner interface.
The ordinary first 20-case control is a bounded development measurement,
not human qualification or proof of population p95. First 27B+ reasoning-on
milestone remains unchanged; a 9B diagnostic or native voice release cannot
complete it.

## Verification and durable next action

Focused B60 checks pass 75 inference and 24 runner/recovery tests. Owner
admission nine and clock six tests pass; the other unchanged targeted answer,
routing, join and observation suites are rechecked separately. Broad Adaptive
discovery has seven import errors from missing pydantic/httpx; no whole-suite
pass or package installation is claimed. Full checkout is read-only in this
heartbeat and does not yet contain these five imported owner files or the two
diagnostic tests. Do not combine checkout test totals.

No live LAN/device probe was needed to review these published contracts.
No service, schedule, package, mount, download, credential, lease or GPU change
occurred. Next continuation: fetch all three branches, consume corrections and
live acceptance evidence, test exact source pins and integrate the published
owner adapter. Until then the old coordinator remains prohibited and model
testing remains BLOCKED. This record does not claim background execution or
receipt by peers simply because it is published.
