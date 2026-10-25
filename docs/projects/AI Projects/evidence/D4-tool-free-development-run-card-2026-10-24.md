# D4 tool-free development evaluation run card — 2026-10-24

## Purpose and status

This card defines one development-only pass over the twelve reviewed,
public-synthetic D4 investigation fixtures. It is **prepared, tested and not
authorized to execute**. The run measures whether the accepted production
local model can investigate the frozen simulated evidence without effects. It
does not qualify a sysadmin role, grant a tool, change routing or select a
provider.

The exact run digest is
`8db6fdee02f55a14c8a1bbfa52ea96307cb716ac33b7780905322883fe2b563b`.
The dry run accesses no key and makes no request.

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
- The run manifest also binds SHA-256 values for all seven executor, engine,
  request, journal and validation modules.

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

One later approval may authorize temporary package staging in LXC104 and this
exact 12-session run. It does not authorize a second attempt, reasoning mode,
connected tools, new credentials, service restart, configuration change,
production deployment, automatic routing, holdout access or a Git push.
