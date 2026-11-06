# M3 K1 constrained 9B preregistration — 2026-11-06

**Result: source-only candidate frozen; no model call or routing effect.**

K1 is materially different from J2 and the five closed successor probes. It
uses the already accepted production 9B/SYCL service as a fixed, temperature-0,
label-only ontology classifier. It performs no training, fine-tuning, retrieval
or free-text reasoning and retains no chain-of-thought. The backend may not be
replaced or restarted for this candidate.

The prompt and output schema must be hash-pinned before any call. Each of the
192 frozen development cases receives exactly one request, with zero retries.
The candidate must reach at least 174/192 exact and satisfy confidence-policy
v2 at 116 or more accepted cases, at most 10% accepted error, zero unsafe false
routes and zero routed privacy underclassification. Results cannot be used to
repair the prompt. Only a passing frozen development run may open the existing
sealed 32-case evaluation once.

Because K1 calls the B60 stack, a later run must use a registered hash-pinned
workload, an exact Lab Hours booking, whole-host lease and shared operation
lock, with accepted-service restoration. This preregistration creates none of
those effects and authorizes no model call, deployment, tools, route or
promotion.

Frozen source evidence:

- canonical preregistration manifest SHA-256:
  `426980258a2830ce754793c0ba08e32c763b1e0927f846e9e313f0a426d8da22`
- validator SHA-256:
  `a98e2731c5c0d44f42335fdaf5dd57e2859bc6f124497b2771c89a9a9e5fba56`
- test SHA-256:
  `84952786a09e9acafb48c5dffaad2a5d3fd817d05e75f0527909aec75435a617`
- focused tests: `5/5` passed
- syntax compilation: passed with an isolated bytecode cache
