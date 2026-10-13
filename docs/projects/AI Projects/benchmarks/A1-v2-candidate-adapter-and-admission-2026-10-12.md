# A1 v2 candidate adapter and Aster-path admission contract

> **State:** Proposed offline contract, 2026-10-12. No candidate endpoint,
> lab lease, raw-evidence transfer, live invocation, automatic route, tool or
> release is authorized by this page. Aster Adaptive owns requests, custody,
> capture and review. B60 owns candidate stack and runtime provenance.

## Decision this contract must support

Can a *named* candidate improve or preserve the accepted 9B's completed-answer
quality on the same fictional requests while respecting privacy, authority,
latency and resource limits? The [A1 v2 control](../experiments/a1-answer-holdout-v2/RESULT-2026-10-12.md)
is a one-session direct-backend development baseline. Its two AI-authored cases
per family and AI reviews cannot establish a class release floor, stable p95,
native Aster latency or sysadmin competence. A paired result using this set is
regression evidence; a route promotion still needs fresh independent labels,
representative load and shadow observation.

## Owner-held request and response boundary

The Mini retains the candidate-visible `cases.jsonl` (SHA-256
`8c5293382a457cbcf4f9999a8904820d6b1d126477fbfc6b672b41a87b62cab9`)
and hidden key outside Git. The adapter receives one validated case object at
a time from `holdout_answer_capture.load_cases`. The only case fields are
`id`, `class`, `fictional_user_request`, `frozen_clock`,
`synthetic_source_records`, `private_context_locality_constraint`,
`permitted_capability_set` and `maximum_tool_scope`; the last must equal
`none`. It must not receive expected answers, rubric items, previous 9B
answers or reviewer judgments. Candidate-specific serialization may change
the API envelope, but not the semantic user request, frozen clock or allowed
synthetic context. Record any system-prompt change as a distinct profile.

Use one no-tool, non-streaming request per case, in frozen order, with a
declared per-request timeout, output-token cap, temperature and reasoning
setting. A response is complete only when the API reports a terminal stop and
the answer is a nonempty bounded UTF-8 string. A timeout, refusal, malformed
output or unavailable endpoint remains an attempt row. Stop on the first
unexpected failure, fill later rows as `not_attempted`, and never retry an
uncertain request. Preserve the existing
`aster-answer-holdout-capture.v1` envelope and all 20 case IDs. Raw answers
and any transport diagnostic go to owner-only storage outside Git; public
exports contain only digests, allowlisted status/error codes, counts and
reviewed metrics. The source-local service credential never enters the case,
model prompt, stdout, trace or repository.

Before invocation, freeze a candidate manifest containing at least:

| Field group | Required binding |
|---|---|
| Candidate | model identity and artifact hash, quantization, context window, reasoning mode, output cap and sampling settings |
| Runtime | binary/build, unit/config, adapter and prompt hashes; exact hardware/device placement |
| Boundary | endpoint identity, TLS/auth method, local/cloud egress, provider retention, tool mode `disabled`, allowed caller and quota |
| Measurement | case/scorer/capture hashes, timeout and batch deadline, clock boundary, load/cache state, warmup and one-attempt order |
| Operations | lease receipt/expiry, completed backup-chain evidence, pre/post service health, recovery owner and abort conditions |

The manifest is immutable for a batch. A changed prompt, model, runtime,
reasoning setting or token limit starts a new series. The current 9B control
profile is not silently rewritten to match a candidate. Aster checks the
manifest and actual endpoint/runtime pins immediately before sending case 1.
If any check is unavailable, the card is `BLOCKED` and makes zero model calls.

### Offline durability candidate

[`journaled_holdout_capture.py`](../../../../scripts/aster-adaptive/journaled_holdout_capture.py)
is a new, unconnected wrapper around the existing capture schema. It creates
an owner-only evidence directory and fsyncs an `attempt_started` event before
each adapter call. It fsyncs a returned answer or allowlisted error before
starting the next case, then atomically seals the ordinary
`aster-answer-holdout-capture.v1` envelope. A process interruption after a
start leaves an explicit uncertain attempt in the journal; the directory
cannot be reused and the code has no retry path. An evidence-write failure
stops the batch even if the underlying capture would classify an ordinary
`OSError` as endpoint unavailability. Six offline tests cover interruption,
post-call storage failure, final-envelope write failure, successful envelope
compatibility, redaction of exception text and deadline rejection before a
call; all 20 focused holdout tests pass.

The journal contains raw fictional answers and is **not** a shareable score
artifact. Its local fsyncs reduce evidence loss but do not prove a recoverable
backup or recover an answer lost between the remote call and local write. The
wrapper has no endpoint adapter, authentication, lab admission or automatic
promotion logic; it is not connected to a live service.

## Full-path admission is a separate measurement

The existing ASGI wrapper measures app entry to first/final body in offline
tests. The A1 v2 control measures direct backend request to terminal response.
Neither starts when Companion accepts a user's ask or ends when the answer is
displayed. A future full-path attempt needs one opaque request ID linking:

1. client accepted timestamp and final displayed/failed timestamp;
2. gateway accepted, route, context/retrieval, backend dispatch, first body and
   final body timestamps where directly observed;
3. exact runtime-profile binding and terminal capture row; and
4. later reviewer outcome without prompt/answer text in shared telemetry.

Use monotonic deltas within each process. Cross-host wall clocks identify
events but do not establish latency without measured synchronization error.
Unobserved phases are `null`, never zero. An interrupted stream or timeout is
censored and cannot be called a slow successful answer. First-token and
terminal-observed times are diagnostic; completed-*useful*-answer time is
reported only after a bound review label. Admit a synthetic no-tool Aster
path first; ordinary Companion/voice timing and cloud/Codex comparisons need
their own consent, identity and transport checks.

The offline [ASGI observation-ID extension](../evidence/A1-private-review-and-asgi-clock-2026-10-12.md)
and [strict content-free join](../../../../scripts/aster-adaptive/join_aster_clock.py)
exercise this boundary with synthetic responses. They do not provide a native
Companion producer, a live service measurement or a useful-answer label.

The [synthetic client-clock pair](../../../../scripts/aster-adaptive/synthetic_client_clock.py)
adds an in-process, marked-fixture display callback using the B60 client's
clock producer from coordination commit `779af42f`. Six offline cases cover
completed display, renderer failure after gateway completion, interrupted
stream, oversized body, an unawaited renderer and rejection of an unmarked
app. A terminal gateway response without a completed display is censored;
neither terminal response nor display establishes answer usefulness. The
fixture marker is a test guard, not a production security boundary. This
copy is attributed to the B60 owner and does not imply a deployed client hook
or native Mac display measurement.

## Live gate and current disposition

A candidate run card can become `READY` only after the platform owner publishes
a verified whole-host lease receipt/expiry/recovery contract and reviewed
candidate staging/endpoint. Recheck the completed backup chain, conflicting
workloads, News reservation, exact pins, health, inference occupancy and
evidence-directory writability just before use. Bound the batch to 20 cases,
one attempt each, declared timeout and wall deadline; reserve restoration
time before 04:15 Vancouver. Abort on hash drift, service restart, unexpected
queue/load, lease conflict, evidence failure, secret exposure or health
regression. Afterward, verify accepted production restoration independently.

**Current status: BLOCKED.** The B60 receipt validates public score integrity
but does not provide a staged candidate or lab authority. Protected-evidence
backup for the original nine-file fictional set is now verified by a
[same-site restore and encrypted off-site byte check](../evidence/A1-protected-evidence-TrueNAS-restore-2026-10-13.md).
No human adjudication, live full Aster-path clock,
per-class current-control distributions or numeric quality floors exist.
Document and resolve these independently. Do not call the 14/20 aggregate a
promotion threshold or convert 20 direct-backend calls into a population p95.

The original evidence directory remains outside the documented Mac pull;
the specifically approved nine-file copy under `~/lab/private-backups` is
what the verified TrueNAS and off-site jobs covered. This proves present
recovery for that set, not future retention or any later model run. Keep the
source and protected copies. The
[protected-evidence backup plan](A1-protected-evidence-backup-plan-2026-10-12.md)
remains the custody boundary for additional evidence.
