# A1 assistant-answer holdout v1 — bounded development run card

**State: attempted once and closed after local evidence-write failure.** It
was READY at 16:57 America/Vancouver, 2026-10-12, then invoked once; see the
[failure result](RESULT-FAILED-2026-10-12.md). This card describes one direct accepted-9B
development comparison. It does not authorize a whole-host lease, model
switch, gateway deployment, native Companion traffic, connected tools or
automatic routing. The separate SA3 sysadmin run has ended and its owner
confirmed release. Stream A independently rechecked live occupancy.

## Question and evidence boundary

Can the accepted local 9B answer or appropriately abstain on the 20 sealed,
fictional assistant requests under the same no-tool prompt strategy used in
the exposed six-case probe? This run can identify answer errors and supply a
fresh **direct-backend** control observation. It cannot establish native
Aster/Companion end-to-end latency, real-world safety, stable p95 or a route
promotion. The held-out answer key and review receipts must never be supplied
to the candidate or runner.

## Freeze before admission

- Candidate-visible cases SHA-256:
  `4b9ca94714414248d3f429237f7385f27ddd132d4f6825676349b85cb5ccc7ae`.
  Hidden key SHA-256:
  `27b6049546abcda89a0c725fffad3452fc6a58ce2595e87a73560545a0933744`.
  [Custody record](../../benchmarks/answer-holdout-release-v1-2026-10-12.md).
- Exact accepted model, quantization, reasoning mode, runtime/binary hash,
  service unit, model path/hash, system prompt, temperature, token cap,
  timeout, endpoint and API semantics: [frozen profile](../../benchmarks/a1-answer-holdout-9b-profile-v1.json)
  SHA-256 `712b0d469e4e35cc3bf2a1cb324014a3390aa1e04b06b1832fbcbf4d0474a349`.
  This is the accepted reasoning-off 9B control, not a reasoning-on candidate.
- Scorer revision, blinded output packet, independent answer-review roles and
  case order/seed: **PENDING**. Case order and labels are frozen in the sealed
  bundle; the execution order and scorer must be declared before output.
- `holdout_answer_capture.py` is a tested label-blind capture primitive: it
  accepts only the exact candidate-visible digest, requires an explicit
  profile hash, records one row per planned case, stops after first failure,
  and saves raw answers in a new owner-only directory. A narrow
  `holdout_answer_9b_adapter.py` now builds the existing accepted-9B-style
  no-tool request from only candidate-visible fields. Offline tests verify
  that rubric and label fields cannot enter the payload and malformed terminal
  responses fail. It has not been used against the live service; freeze its
  source and verify the actual accepted profile before invoking the holdout.
- `prepare_holdout_answer_review.py` is a tested post-run handoff primitive.
  Only after the raw-attempt digest is sealed, the custodian joins the hidden
  key to backend-blinded answers in a private review packet and blank rubric
  template. It emits no case or answer text to Git or stdout. A completed
  independent judgment is still missing; the template is not a score. The
  offline `score_holdout_answers.py` checks a review against the exact packet
  digest and separates expected outcome, rubric failures, prohibited claims
  and privacy violations. Its reviewer ID is a claim, not verified identity.
- No connected tools, real personal context, live web or infrastructure
  actions. Synthetic context is supplied only in the candidate-visible case.

The one-shot transport source SHA-256 is
`633ed3e0ac19f0c62509c57750f63ab7a0a0d20a3d602df72bfedd61cbca7a0c`.
It sends only candidate-visible fictional cases; the API key is read inside
LXC 110 by its existing service account. Raw answers return only to a new
mode-0600 file under the Mac's owner-only Aster evidence directory. The
transport has no automatic retry and refuses an existing output directory.

The current offline source candidates have these SHA-256 pins; recheck and
freeze them at admission rather than relying on a branch name:

| Source | SHA-256 |
|---|---|
| Label-blind capture | `1cb134d7cb64beaf2e4159219e912b48e5a4244a1c1c7ee3792bf9ff662f1728` |
| Accepted-9B request adapter | `a8b0a03b57d04b48ce4614b125f2ef52a369fc3d3a27c3d962f467a1876235b1` |
| Private reviewer packet | `5261b63844b4c35724824df3941d6e645534f7ea16a5fc9822197b17961e05ce` |
| Content-free scorer | `5c028cdf0f8c37d036e73e7597810d31a2eb723bc8e7cc849a8512e0fa01c263` |

## Admission and stop checks

1. Obtain the platform owner's current lab/lease status. Do not overlap its
   SA3 run, host-level lease, backup or runtime change. Verify service health,
   expected model/profile and idle processing/deferred queues immediately
   before a shared-service probe. A historical idle check is not admission.
2. Validate the protected bundle and digest locally. Transport only the
   candidate-visible cases. Keep the local service credential inside its
   existing source-local boundary; never copy it into Git, prompts or logs.
3. Use serial requests, one attempt per case, fixed timeout and bounded
   total wall time. Preserve a row for every planned case, including skipped
   cases after a stop. Stop on model/service restart, drift, occupancy/lease
   conflict, backup collision, unanticipated tool use, secret exposure or
   health regression. Do not retry failures under the same run ID.
4. Store raw fictional answers mode 0600 outside Git and seal their digest
   before the answer key is opened. Export content-free timing/status/provenance
   rows. The reviewer sees backend-blinded answers and frozen rubric; the
   candidate's self-assessment is not a score.
5. Recheck service health, model/runtime pin, restart count and queues after
   the run. Record partial results even if stopped. Compare per class and
   report abstentions, incorrect claims and failures separately from speed.

**16:57 live preflight:** The platform owner explicitly reported that its SA3
activity was finished, the host lease released, accepted 9B inference passed
postchecks and no B60 work was active. Direct read-only SSH found both lease
state and lock absent, LXC 110 running, `aster-llama.service` active with PID
10445 and zero restarts, `/health` OK, zero processing/deferred requests,
and exact accepted unit, binary and model SHA-256 matches. The sampled recent
20 Proxmox tasks had no active task; process-name check found no `vzdump`,
`rsync` or `pbs-client`. The News reservation is 17:15, so this one run must
start before 17:00, has a 10-minute hard batch cap and leaves time for a
postcheck. These are point-in-time checks, not a general lab lease. Recheck
lease and queue immediately before the call; a failed check cancels the run.

## Decision limit

Even a 20/20 rubric pass would only support another paired, consented
qualification step. The corpus is AI-authored/reviewed, only two per class,
and its protected local backup is UNKNOWN. A separate full Aster-path timing
run and independent or human adjudication remain necessary before changing
any automatic route. No permissions follow from answer quality.
