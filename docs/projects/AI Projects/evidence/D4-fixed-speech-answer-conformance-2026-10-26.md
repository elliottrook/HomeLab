# D4 fixed Aster Speech — answer conformance

**Date:** 2026-10-26  
**State:** deterministic conformance passed; independent usefulness open

## Frozen fixture

The synthetic fixture contains eight cases, two for each fixed state: `ok`,
`warn`, `fail` and `unavailable`. Each case contains only the bounded schema-2
observation and a fictional question. Its SHA-256 is
`79c8ac3b8c30b567b5fdabd8fa32209cd586f0e08232ee4b3c158379d691ad27`.

The preregistered conformance gate requires all eight cases to satisfy:

- exact state reporting;
- evidence scoped to `aster.speech` or explicit absence of a speech fact;
- exact observation time and age;
- the fixed cause/repair/broader-health limitation; and
- zero unsafe repair, cause or whole-system claims.

The fixture explicitly requires independent review before claiming usefulness.
It grants no authority and cannot enable routing.

## Result

All **8/8** cases passed all four dimensions with zero unsafe claims. The
machine-readable result is
[D4-fixed-speech-answer-conformance-result-2026-10-26.json](D4-fixed-speech-answer-conformance-result-2026-10-26.json),
SHA-256 `7a9fd844d3679610562c754c806a5a0c43e08b3e03e17b136c3b57645aa1fbbf`.

The focused implementation plus existing fixed Speech boundary suite passes
**25/25**. No broker request, model call, service change or route occurred.

## Next gate

Prepare a digest-bound review packet that hides implementation identity and
the acceptance result, then obtain an independent judgment of whether these
fixed answers are practically useful compared with a generic aggregate-health
answer. Deterministic conformance alone is not a usefulness claim.
