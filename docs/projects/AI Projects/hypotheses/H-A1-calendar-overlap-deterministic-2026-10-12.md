# H-A1 — deterministic calendar overlap before model reasoning

**State:** Hypothesis, not an approved route or calendar integration.
**Trigger:** In the [six-case synthetic 9B answer probe](../experiments/a1-9b-synthetic-answer/RESULT-2026-10-12.md),
the accepted local model cited a fictional 14:00–15:00 appointment yet said
14:30 was free. One exposed case proves a failure on that input, not a class
error rate or that all calendar questions should bypass a model.

**Hypothesis:** For a request that can be normalized to a specific time and
authorized calendar interval, a deterministic overlap calculation can answer
the occupancy part more reliably, faster and with less private-context egress
than asking an LLM to infer overlap from prose. An LLM could still explain a
computed result or handle a broader planning question, but cannot override
the normalized fact or invent an action. If parsing, timezone, recurrence,
calendar freshness or target identity is uncertain, the skill abstains and
asks for clarification or routes to a higher-level, policy-permitted path.

**Proposed experiment, before implementation/promotion:**

1. Define typed event intervals, requested interval/instant, timezone,
   all-day/recurrence semantics, freshness and calendar identity; specify
   unavailable/ambiguous input as a first-class outcome.
2. Build an independent synthetic set with boundary instants, overlapping
   events, timezones and daylight-saving transitions; keep its labels separate
   from the developer and from model prompts. Include denied calendar access
   and stale data as mandatory negatives.
3. Compare the deterministic candidate with the accepted local model on the
   same observable question. Measure exact occupancy correctness, abstention,
   false-free and false-busy rates, end-to-end latency, local data retention
   and failures. Record distributions and raw errors, not only an average.
4. Require zero observed privacy/permission violations and a reviewed error
   budget before a shadow route. A shadow route must not alter household or
   calendar state. Promotion would be class-specific, reversible, versioned
   in the Capability Registry and separately authorized under Aster policy.

**Potential disproof:** If reliable parsing/recurrence support and secure
calendar access cost more complexity than the narrow request class warrants,
or if the deterministic candidate misclassifies realistic schedules, keep
calendar occupancy as an explicit verified tool result and abstain on the
unsupported cases. Do not broaden model permissions to paper over the error.

**Current evidence threshold:** unmet. The one six-case development run is
an observation that motivates a test, not evidence to change routing.
