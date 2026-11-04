# M3 J2 quality-review contract and candidate-v4 result — 2026-11-04

## Decision

**PASS; CANDIDATE-V4 QUALITY EVIDENCE IS NOW DURABLE AND EXACT-SOURCE BOUND.**

The earlier label-review contract proves the 960 semantic-label decisions but
does not encode its prose-quality judgment. Candidate-v4 was therefore not
handed to the owner on chat evidence alone. A separate source validator now
requires one explicit boolean judgment for grammar, naturalness, semantic-label
quality and split quality on every exact corpus row. Pending values, missing or
duplicate rows, unexplained failures, notes on passing rows, source drift,
reviewer substitution, self-hash drift and authority changes fail closed.

The corpus-release boundary and content-free custody receipt now bind this
quality-review artifact in addition to the corpus, normalized set and semantic
label review. A valid quality artifact with any failed dimension remains
release-ineligible.

## Candidate-v4 result

The fresh reviewer completed all 960 rows against corpus SHA-256
`9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`.
Every one of the four dimensions passed on every row; there are zero grammar,
naturalness, semantic-label or split-quality failures. The owner-only mode-0600
artifact has:

- artifact SHA-256
  `f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f`;
- contract self-hash
  `408e7479e106f614b2a2011da624c10af4ca6919d30d4cccd93dcf242fec4a35`;
- size 128,107 bytes;
- authority `not-granted` and automatic routing `off`.

The complete J2 source suite passes 50/50. This makes candidate-v4 ready for
the owner corpus-release review. It does not authenticate external custody,
authorize training, open the sealed evaluation boundary, call a model, grant
tools, enable routing or create any production effect.
