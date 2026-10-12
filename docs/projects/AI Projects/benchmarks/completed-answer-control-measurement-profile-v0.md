# Aster completed-answer control measurement profile v0

**Status:** Method frozen for planning on 2026-10-12; no qualifying corpus,
latency budget, quality floor, model promotion or live run is authorized by
this document. Aster owns the task measure. B60 owns stack identity and runtime
instrumentation. The six public fictional cases are development examples only.

## Decision the measurement must support

For each request class, can a named local candidate deliver a *useful,
policy-compliant completed answer* at a tolerable delay and resource cost,
compared with the accepted current local path? Aster must be able to say which
classes remain deterministic or require a stronger backend. Faster text
generation alone is not a pass. The accepted 9B control is a stack profile,
not a permanent architectural ceiling.

## Fixed boundaries

- Start the user-facing clock when Aster accepts a request. Stop at the first
  terminal useful answer, justified abstention/clarification, explicit policy
  denial, or terminal failure. Keep an additional terminal-observed clock even
  when usefulness is pending review. A streamed first token is diagnostic, not
  task completion.
- Record route, context, retrieval/tool and inference components **only when
  observed**. `null` means unmeasured, not zero. If the current API lacks an
  Aster-to-answer trace, report its inside-service timing separately; never
  relabel it as end-to-end latency.
- Preserve one row for every planned case/attempt, including failed, timed-out,
  refused and abstained attempts. A timeout is right-censored at its declared
  cutoff; do not substitute the cutoff as a measured completion time or drop
  it from reliability. Keep first attempts distinct from any later retry.
- Freeze the candidate model/quant, runtime revision, binary, unit, prompt,
  adapter, reasoning mode, context, tools, egress and hardware hashes before
  each batch. Reasoning-on and reasoning-off are separate profiles. Pin fixture,
  case-order seed, scorer, policy and capture code hashes. A changed pin starts
  a new series.
- Use the same synthetic request and permitted context for paired candidates.
  Alternate candidate/control order with a recorded seed where practical;
  sample current control before and after the candidate series to reveal
  thermal, load or cache drift. Do not compare different tool access or
  different request boundaries as equivalent.
- Run warm-resident idle and representative shared-load profiles separately.
  Cold/reload is a third profile only if that state is operationally relevant.
  Record load source, concurrency, cache state, warmups, token cap, timeout,
  first/last run times, queue depth and service restarts. Do not create load
  against production without its own bounded run card and lease checks.

## Labels and review custody

The case author freezes expected observable behavior and prohibited claims
before any candidate output is seen. A reviewer other than the case author
should score backend-blinded answers where practical, item by item, against
that rubric. A second reviewer resolves safety or class-boundary disagreement;
retain both initial labels and the resolution. The reviewer may see the
synthetic context and timestamp but not model identity or a model's self-score.
Record four distinct outcomes: useful completion, justified
abstention/clarification, correct policy denial, and failure/incorrect answer.
An abstention or denial can be the correct outcome for its case, but it is not
counted as an answer to a task that required a substantive answer. Track
prohibited claims and privacy/authority violations separately; a violation
cannot be compensated by speed or other correct items.

For the current v0 synthetic development scorer, `passed` means the supplied
rubric booleans were all true and no prohibited claim was marked; it does not
prove independent review or establish the four outcome categories. Do not
reuse that field as a release metric. Raw synthetic answers stay in restricted
local custody; only content-free attempt, provenance and adjudication records
are shared. Before collecting real interactions, decide consent, retention,
redaction, access and whether even a public hash of a short answer is safe.

## Analysis and stopping

Publish per class and profile: planned/attempted count, useful completions,
justified abstentions, correct denials, incorrect answers, boundary violations,
terminal failures, retries and censored timeouts. For observed terminal time,
show p50/p95 *with sample counts and uncertainty*; for useful completion time,
do not compute a percentile from only successful cases without explicitly
conditioning it on success and reporting the failure fraction. Small samples
may support feasibility or regression debugging, not a population p95.
Provide paired case-level differences and disagreement reasons; avoid
cross-class aggregate scores that conceal calendar or security failures.

Stop a live batch on an unexpected service restart, runtime hash drift,
credential/log exposure, lease conflict, backup/News conflict or material
health regression. Keep partial results and postcheck production. An observed
privacy or authority violation blocks promotion for the affected class until
root cause, fix and fresh independent evidence exist. Model tuning on exposed
development cases cannot turn them into qualification cases.

## Gates still open before a class-specific release bar

1. Independent cases, labels and reviewer custody, including explicit negative
   and abstention cases. The six exposed cases and the nonblind 9B inspection
   cannot fill this gate.
2. Actual Aster-path clock and phase instrumentation, plus a verified local
   invocation-to-profile binding. A user-facing budget needs this boundary.
3. Multiple control sessions in each relevant load/cache profile, with enough
   cases to describe variation. The first six-case 9B run had 0.849–1.750 s
   terminal timings but is warm, exposed and lightly loaded; it is no p95 bar.
4. Jason's already stated target is candidate 27B+ reasoning-on useful-answer
   median and p95 no slower than the fresh accepted-9B control, including
   reasoning and user-facing steps. The per-class **numeric control values**
   and explicit safety/quality floors are still `UNKNOWN`; derive/freeze them
   before seeing finalist scores. Do not ask Jason to choose a slower waiting
   allowance merely because an engineering candidate misses this target.
5. A consented, equivalent Codex comparison if cloud fallback is in scope;
   existing manual Codex questions are not paired with this corpus.
6. A verified lab lease and bounded run card for experiments needing exclusive
   B60 access. A clock window by itself is not a lease.

The immediate next measurement may reuse the public six-case set to verify
capture wiring, reviewer handoff and the B60 wrapper after its source pins are
reconciled. It must be labelled development. A fresh, independently frozen set
is required before any qualification comparison or route promotion.
