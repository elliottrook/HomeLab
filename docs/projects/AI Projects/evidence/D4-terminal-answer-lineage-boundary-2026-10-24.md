# D4 terminal-answer lineage boundary — 2026-10-24

## Finding

The private D4 package already validated the structure and bounded content of an
injected investigation-engine result. It did not bind a terminal `conclude` or
`clarify` status to the final retained answer. A malformed producer could therefore
record `conclude` with no answer, or `clarify` while the final answer declared
`conclude`. A non-transport result could also claim an attempted-call count that
did not match its retained steps.

These inconsistencies would make later scoring and audit ambiguous even though
the JSON was structurally valid.

## Correction and validation

`validate_engine_result` now requires:

- every `conclude` or `clarify` result to contain a final answer;
- that final answer's decision to equal the terminal status;
- a terminal answer to carry no check ID; and
- a non-transport attempt count, when present, to equal the retained step count.

Focused mismatch cases and the complete evaluation suite pass **126/126** under
Python 3.12. The test uses only synthetic fixtures. It reads no private holdout,
contacts no model or service, grants no capability and makes no deployment or
promotion claim.
