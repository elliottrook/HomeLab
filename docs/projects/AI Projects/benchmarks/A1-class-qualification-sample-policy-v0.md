# A1 class-specific answer qualification and sample policy v0

> **Status:** Proposed measurement policy, 2026-10-12. It sets no new model
> release floor, grants no route/tool, and does not admit a live experiment.
> Jason owns the final waiting-time and risk decision. Aster owns class labels
> and evaluation; B60 owns candidate performance engineering.

## Unit of decision

Decide separately for each request family and exact stack profile. The A1 v2
fictional set has two cases per family and is an immutable *development
regression* set after the accepted 9B result was inspected. Its 14/20 overall
score cannot be a release bar. A candidate can improve the aggregate while
making calendar-plus-web, privacy or denial behavior worse. Outcome categories
remain useful completion, justified abstention/clarification, correct denial
and failure; mandatory authority/privacy violations are counted separately.

| Family | Primary evidence before any earned route |
|---|---|
| Timer, lighting, media | Correct intent/effect boundary, no fabricated execution, and deterministic-skill control. An LLM must add value over the existing skill. |
| Stable fact, frozen web | Correct answer or justified uncertainty with source freshness; no invented citation or live-web claim from frozen context. |
| Calendar and calendar plus web | Correct time arithmetic, event conflict and source combination; no claim that a calendar or website was consulted unless it was actually supplied. Mixed cases are a separate slice. |
| Fictional personal context | Locality and minimization first; no cloud transmission or memory claim outside the recorded consent/context boundary. |
| Sanitized HomeLab diagnosis | Accurate, evidence-linked read-only finding; no claimed action or generic sysadmin authority. Technical outcome review is separate from answer style. |
| Ambiguous or unsafe | Correct clarification, abstention or denial; no permission escalation. These are successes when the case expects them, not useful substantive completions. |

## Freeze the bar before a challenger

For each family, pre-register the intended user-visible outcome, accepted 9B
control profile, paired candidate profile, independent case source, human
label rubric, hard privacy/authority constraints, acceptable quality loss or
required gain, user-facing p50/p95 waiting-time limits, resource/cost ceiling,
observation window, stopping rule and rollback. Numeric limits remain
**UNKNOWN** until the current Aster path is measured in relevant warm and
shared-load conditions and Jason accepts the class's waiting/risk tradeoff.
Do not choose a looser 9B control after seeing a slower challenger.
Jason's stated engineering target for a reasoning-on 27B+ candidate is no
slower completed useful answers than the fresh accepted-9B control; this
cannot yet be reduced to numeric per-class limits because the full-path
control has not been measured.

Use fresh cases authored without seeing the finalist output, and hold rubric
keys outside model prompts and candidate engineering. Separate development,
calibration and locked qualification partitions by scenario/template and time.
Variants of the same incident are a group, not independent samples. AI-derived
labels may triage review, but a qualification label needs a human adjudicator
who was not the case author; safety and technical disagreements receive a
second independent judgment. Retain initial labels and resolution. Do not use
the locked set repeatedly for prompt or model tuning; a materially adapted
candidate needs a fresh locked set.

## Sample size and uncertainty

Plan sample size from a **predeclared** maximum acceptable error, expected
control rate, smallest worthwhile paired improvement, and desired uncertainty.
Do not use a fixed global “20 cases” or “two sessions” rule. Report planned,
attempted and completed counts by family and load/cache profile, including
timeouts, refusals, stopped batches and abstentions. If a case family is too
small to distinguish candidates, the decision is **INDETERMINATE**, not PASS.

For intuition only, if independent representative trials showed zero failures
in `n` attempts, solving `(1-p)^n = 0.05` gives the one-sided 95% upper bound
`p = 1 - 0.05^(1/n)` on the failure probability:

| Zero-failure attempts in one homogeneous slice | Upper bound |
|---:|---:|
| 2 | 77.64% |
| 20 | 13.91% |
| 59 | 4.95% |
| 299 | 1.00% |

Those bounds **do not** apply directly to the A1 v2 set: it is AI-authored,
has different families, and does not have independent representative sampling.
Even 59 trials without a violation would not prove a policy boundary is safe;
deterministic enforcement and adversarial review remain mandatory. The table
shows why two good examples cannot justify automatic privilege or routing.

For paired quality, compare case-level outcomes on the same inputs and report
per-family differences and uncertainty with scenario groups kept together.
Do not drop failures or timeouts from latency analysis. Report terminal-time
distributions and completed-*useful*-answer distributions separately, with
their denominators and censoring. A percentile from only successful calls is
conditional on success and must be accompanied by the failure fraction. A
single warm session does not establish a population p95. Run control before
and after candidate sessions to expose drift and keep cold, warm and shared
load distinct.

## Promotion decision

Any confirmed permission, privacy, false-action or secret-handling violation
blocks the affected route until root cause, deterministic correction and fresh
independent evidence. An exact stack can be **PROMOTED** only for named
families when preregistered quality, latency, cost, reliability and hard
constraints pass, an effect-free shadow period finds no new regression, and
the normal policy/approval gate permits a reversible canary. A result may be
**REJECTED** for a measured regression or **INDETERMINATE** for insufficient
samples, uncertain labels or failed evidence custody. Probationary models get
no new tools from an answer score. Keep the accepted control and rollback
available and continue monitoring after any class-specific change.
