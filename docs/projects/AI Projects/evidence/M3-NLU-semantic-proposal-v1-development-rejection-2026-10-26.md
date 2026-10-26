# M3 NLU semantic-proposal v1 — public-development rejection

**Date:** 2026-10-26  
**Decision:** reject before calibration

## Architecture tested

This candidate implemented the architecture correction after Candidate-v10.
The accepted local 9B model could emit only six non-authorizing semantic slots:
action, domain, privacy hint, referent completeness, safety override and
multi-source composition. It could not emit a disposition, capability,
sensitivity decision, authorization or route. Deterministic code alone owned
privacy floors, deny/abstain/clarify, capability allowlisting and route
eligibility.

The source-only boundary passes six focused tests; the bounded runner passes
three tests and the existing deterministic guard passes nine. The exact source
hashes were:

- semantic proposal/policy SHA-256:
  `85683a7b01ad24d438fe54c7ce749921aa8d5f2e22924b7d02435054e29a363b`;
- public-development runner SHA-256:
  `1118352f85d59f64b0a7ae34f69e4015c2c5347e84254690195b0e12e9875541`.

## Public synthetic run

Jason's standing authorization permits bounded use of the already-running AI
stack when no service restart is required. Fresh checks found the whole-host
lease ready, LXC110 running, `aster-llama.service` active and its restart count
zero. The exact 24-case public synthetic development fixture ran once. It did
not use a private calibration or holdout and could not execute a route.

Content-free result:

- attempted and structurally valid: **24/24**;
- exact interpretations: **9/24**;
- routed: **15/24**;
- safe and exactly correct routed: **6/15**;
- unsafe false routes: **0**;
- routed privacy underclassifications: **0**;
- run SHA-256:
  `484045ccc24f614898b9429511f6f996187f32081121e52fe114dced5aeef890`.

The registered public-development gate required at least 23/24 exact with zero
unsafe and privacy failures. Safety held, but semantic accuracy failed by a
wide margin. Frequent content-free mismatch dimensions were family/capability
for general answers, external research and service changes, plus incorrect
handling of incomplete referents. The candidate is therefore rejected without
prompt repair, private calibration, threshold selection or holdout access.

The llama service remained active with zero restarts and the lease state
remained ready after the run. No schedule, service, key, grant, route or
production file changed.

## Next architecture gate

Do not iterate this semantic-slot prompt on another independent corpus. The
next challenger must change the representation itself, such as a dedicated
embedding/encoder model or a demonstrably stronger local model family, while
retaining deterministic policy ownership. It must first clear the exposed
public and six spent development sets before any new calibration is justified.
