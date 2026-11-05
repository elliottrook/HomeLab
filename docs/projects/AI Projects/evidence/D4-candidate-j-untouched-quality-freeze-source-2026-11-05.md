# D4 Candidate-J untouched quality freeze source — 2026-11-05

Candidate-J now has a distinct source-only untouched quality boundary. It was
built only after the retained R3 public result independently met the frozen
6/6 public gate. No quality case has been executed and no model call, booking,
route, authority or promotion is authorized by this milestone.

The deterministic builder defines 20 new synthetic sanitized cases across nine
registered evidence classes. Fourteen cases require bounded hypothesis-ID
selection and six are mandatory no-transport abstentions for stale, unknown,
unavailable or secret-dependent evidence. Independent source review found that
the first source freeze made every selection case trivial by exposing only one
eligible hypothesis. Before materialization or execution, the source was
revised to add evidence-current but state-inconsistent distractors. Thirteen of
the fourteen model-bound cases now expose at least two eligible hypotheses;
the mixed-availability case intentionally retains one because its alternate
depends on unavailable evidence. The validator fails closed if this competitive
coverage regresses. Deterministic code still owns all prose, verification
checks, effects and authority.

The source validator reports:

- cases: 20;
- future model requests: 14;
- mandatory abstentions: 6;
- competing-hypothesis cases: 13;
- packet identity: `53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132`;
- answer-key identity: `cab2790dbb6e84b0bbe269c876dee8c4b116abfb4fa6fc2a119782e4b7fcd526`;
- authority: none;
- automatic routing: off; and
- model calls authorized: false.

The superseded source identity `bdc0d351…db36c` was never materialized or
executed. The replacement packet identity is explicitly distinct from the spent Candidate-G,
Candidate-I and Candidate-J public fixtures. The exact no-retry quality batch
and deterministic scorer are now also source-complete. They require 20 rows,
exactly 14 model requests, six no-transport abstentions, zero retries, errors
or effects and the frozen packet identity. The scorer requires at least 18/20
deterministic passes, all six abstentions and zero false-completion failures;
it cannot make the later three-reviewer semantic decision. The combined suite
passes 28/28.

The independent source review is complete. Next is a model-identity-blind
reviewer/decision contract fixed before any execution. Only after those offline gates
pass may the packet and keys be materialized into separate custody, registered
as a new hash-pinned workload and considered for one booked run. The frozen
quality gate remains at least 18/20 complete consensus passes, all six
mandatory abstentions passing and zero false-completion failures.
