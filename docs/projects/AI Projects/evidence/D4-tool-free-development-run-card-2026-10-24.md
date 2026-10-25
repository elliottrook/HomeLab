# D4 tool-free development evaluation run card — 2026-10-24

## Purpose and status

This card defines one development-only pass over the twelve reviewed,
public-synthetic D4 investigation fixtures. It is **prepared, tested and not
authorized to execute**. The run measures whether the accepted production
local model can investigate the frozen simulated evidence without effects. It
does not qualify a sysadmin role, grant a tool, change routing or select a
provider.

The corrected exact run digest
`d61be2b4165a19498808226e2b2118dddd1899b379d87997d0ff098232657d2e`
was executed once and is spent. It completed twelve first calls but all twelve
results were `invalid_answer`; see the
[attempt 2 result](D4-tool-free-development-attempt-2-result-2026-10-24.md).
There is no authorization to replay it.

## Frozen inputs and runtime

- Reviewed fixture file SHA-256:
  `c3999bdd26d66290fb751519fc2439d28f45bc9fde4e13a76bc6a1afae4faf58`.
- Fixture review SHA-256:
  `59aee3a99826a75423327ab614676b31daa44f8879f4b602898ad101287ed07f`.
- Reviewed corpus file SHA-256:
  `85e511b8470bbfb753f30668c1589259e73518d92b1e281008aaa7bd0cc0fbbb`.
- Content-free plan file SHA-256:
  `387fdf869d697295fea17736c14241f94b6c62af92067cd91d8fa4555da50791`.
- Model/API name: `qwen3.5-9b`.
- Required live runtime: Qwen3.5-9B Q4_K_M, llama.cpp b11429,
  SYCL/Level Zero, accepted production unit and existing bearer identity.
- Mode: `nonthinking` only. The accepted service is explicitly reasoning-off;
  this card does not pretend that a compact-thinking comparison is available.
- The run manifest also binds SHA-256 values for all eight executor, engine,
  request, journal and validation modules.

The first approved staging attempt for predecessor digest `8db6fdee...` stopped
at the target dry run before authentication because the package omitted the
transitive `validate_sa3_holdout_release.py` import. No model request ran. The
temporary package was removed and production stayed healthy. The revised
manifest includes that module, adds an isolated-package import-completeness
test and passes the complete 141-test suite. The predecessor approval is spent
and does not authorize this revised digest.

The next approved execution at predecessor digest `6299c6b2...` completed all
twelve sessions but every first response was rejected for citing unobserved
evidence. The [attempt record](D4-tool-free-development-attempt-1-result-2026-10-24.md)
preserves the bounded measurements and immutable ledger identity. The current
candidate constrains `evidence_ids` to the IDs actually revealed at each step,
while retaining the independent fail-closed engine check. It also reports
accepted-terminal session counts explicitly, so schedule completion cannot be
mistaken for a quality pass. The complete suite passes 142/142. The prior
approval is spent and does not authorize the corrected digest.

The corrected `d61be2b4...` execution also completed its twelve-session
schedule, but all twelve first responses failed the answer-shape boundary. The
private journal intentionally discarded those malformed bodies and could not
separate invalid JSON from a wrong field/type shape. A one-call content-free
[contract probe](D4-one-call-contract-probe-card-2026-10-24.md) is now the next
candidate. Another full development run is not justified until that probe
identifies and a tested correction closes the exact contract failure.

The approved [one-call probe](D4-one-call-contract-probe-result-2026-10-24.md)
measured `duplicate_evidence_id`: the accepted llama.cpp path did not enforce
the schema's `uniqueItems` constraint. The next offline candidate
canonicalizes repeated citations in first-seen order, records only the count
removed, and still rejects every unobserved citation. The complete suite passes
148/148. Its exact run digest is
`9a089af8bf599bfbea35bc1ead7ea70d93c52f6345c7aeee2d40d77c118b2078`.
It is prepared but not authorized to execute.

That `9a089af8...` candidate subsequently ran once. The
[attempt 3 result](D4-tool-free-development-attempt-3-result-2026-10-24.md)
accepted the full two-check investigation path in ten cases and retained one
terminal answer, but rejected eleven terminal decisions whose unused `check`
field was nonempty. The next candidate clears that advisory string only for
terminal decisions and records the normalization; actual check decisions keep
all capability controls. The suite passes 148/148 and the new exact digest is
`8f0cd102953d4b830e19b18bc4511bc2f9742356156d45d6f2fcbfee53d80c72`.
It is prepared but not authorized to execute.

The `8f0cd102...` candidate subsequently ran once and passed the execution
boundary with 12/12 accepted terminal answers; see
[attempt 4](D4-tool-free-development-attempt-4-result-2026-10-24.md). Its
authorization is consumed. Its subsequent
[model-blind review](D4-tool-free-development-attempt-4-blind-review-2026-10-24.md)
was a semantic NO-GO: verification passed 0/12 and diagnosis passed 8/12.

Candidate-B required each terminal answer to state its discrimination and an
explicit unperformed verification. Its approved attempt completed all twelve
calls but structurally admitted only one: eleven check requests also populated
the terminal-only advisory fields. Those answers were discarded and no blind
review ran. Candidate-B is spent.

Candidate-C cleared correctly typed nonterminal advisory fields before
retention. Its approved run stopped during the first case because the outer
journal validator did not yet allow the new content-free normalization flag.
Its single start marker makes that journal uncertain and permanently
non-resumable. Candidate-C is spent.

Candidate-D adds the missing outer-validator allowance and Boolean type check,
with an integration test across that boundary. It is preregistered at exact
digest `55d85c44…e99`. Its approved run completed 12 sessions and 31
calls, structurally accepted eight terminal answers and rejected four terminal
answers that omitted a required discrimination or verification string.
Candidate-D is spent and no blind review ran.

Candidate-E requires nonempty advisory strings in the constrained JSON grammar
for every decision. Nonterminal values are still cleared before retention;
terminal values remain available to the blind reviewer. It is preregistered at
exact digest
`0e6b324a5e779b00744f9258431280016116df75e1f7cccd67d0e383545104d6`.
Its eleven-file source manifest has SHA-256
`3c46f8de30b871623663cda288623fc55a6bc8348ed044f7b75ac95b319ca4fe`,
and the complete suite passes 164/164. It has not run.

## Bounded execution

- 12 cases, one session per case, fixed source order.
- At most two simulated checks and three model calls per case.
- At most 36 model calls in total.
- Each request has a 60-second timeout, matching the reviewed case protocol.
- Each case has a 180-second total budget.
- Temperature zero; no retries after an uncertain or transport-failed session.
- The executor checks authenticated health and a single zero
  `requests_processing` gauge before every case. If shared inference is busy,
  it records a content-free pause and stops before another request.
- The hash-chained journal is owner-only. Raw reasoning is discarded; retained
  rows contain bounded metadata, simulated observations and the returned
  advisory answer.

## Fresh gates immediately before execution

1. The exact run digest and every source hash still match.
2. `local-ai-lease status` is `ready`; no lab lease, backup, maintenance or
   competing model experiment is active.
3. LXC110's accepted `aster-llama.service` is active with zero restarts and the
   exact Qwen3.5-9B Q4_K_M / b11429 / SYCL / reasoning-off command line.
4. Aster Agent and Speech are healthy, the model endpoint is authenticated and
   idle, and the run will not overlap the News workload or its safety margin.
5. A temporary hash-verified package and root-only journal location exist in
   LXC104. No production source or unit is replaced.

On 2026-10-24 at 20:05 Vancouver, read-only preflight observed the lease ready,
the accepted LXC110 command line active/running with zero restarts, and Aster
Agent, Speech, `pvescheduler` and `pvestatd` active. These observations are not
substitutes for the fresh execution gates.

## Stop and postcheck

Stop without replay on a hash mismatch, busy service, unhealthy dependency,
timeout, transport error, malformed response, tool output, effect claim,
unobserved citation, uncertain journal state or schedule conflict. Do not
change the model, unit, key, firewall, lease or backup schedule to make the run
pass.

After the last session, require the service to be healthy and idle, verify no
service restart or accepted-runtime drift, preserve the root-only journal and
remove only the temporary source package. Produce a bounded execution report.
Human, model-blind answer review remains required before any quality claim.
Development results cannot satisfy the independent 20-case holdout or promote
the model, route, tool authority or repair capability.

## Approval boundary

The authorizations for attempts 4 through 7 have been consumed. Candidate-E's
exact 12-session run is not authorized. Any later authorization would cover only
the candidate-E digest and bounded execution above; it would not authorize a replay,
reasoning mode,
connected tools, new credentials, service restart, configuration change,
production deployment, automatic routing, holdout access or a Git push.
