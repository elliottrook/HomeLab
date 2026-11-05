# D4 Candidate-J untouched quality freeze source — 2026-11-05

Candidate-J now has a distinct source-only untouched quality boundary. It was
built only after the retained R3 public result independently met the frozen
6/6 public gate. No quality case has been executed and no model call, booking,
route, authority or promotion is authorized by this milestone.

The deterministic builder defines 20 new synthetic sanitized cases across nine
registered evidence classes. Fourteen cases require bounded hypothesis-ID
selection and six are mandatory no-transport abstentions for stale, unknown,
unavailable or secret-dependent evidence. Deterministic code still owns all
prose, verification checks, effects and authority.

The source validator reports:

- cases: 20;
- future model requests: 14;
- mandatory abstentions: 6;
- packet identity: `bdc0d351a8554473d1ade6794abdd87dc5bffa1c3067b22921f4f9d96abdb36c`;
- answer-key identity: `cab2790dbb6e84b0bbe269c876dee8c4b116abfb4fa6fc2a119782e4b7fcd526`;
- authority: none;
- automatic routing: off; and
- model calls authorized: false.

The packet identity is explicitly distinct from the spent Candidate-G,
Candidate-I and Candidate-J public fixtures. The exact no-retry quality batch
and deterministic scorer are now also source-complete. They require 20 rows,
exactly 14 model requests, six no-transport abstentions, zero retries, errors
or effects and the frozen packet identity. The scorer requires at least 18/20
deterministic passes, all six abstentions and zero false-completion failures;
it cannot make the later three-reviewer semantic decision. The combined suite
passes 27/27.

Next is an independent source review and a model-identity-blind reviewer/
decision contract fixed before any execution. Only after those offline gates
pass may the packet and keys be materialized into separate custody, registered
as a new hash-pinned workload and considered for one booked run. The frozen
quality gate remains at least 18/20 complete consensus passes, all six
mandatory abstentions passing and zero false-completion failures.
