# D4 fixed Aster Speech — offline selector boundary

**Date:** 2026-10-26  
**State:** source-only; automatic routing remains off

## Result

`scripts/aster-adaptive/fixed_speech_selector.py` connects the formal NLU
contract to the activated fixed Speech result without granting execution
authority.

It proposes the local `aster-fixed-speech-caller` backend only when a validated
`request-interpretation.v1` is all of:

- family `read-only-investigation`;
- sensitivity `public` or `internal`;
- exactly one capability need, `diagnostic.aster-speech.latest`;
- clear, understood and disposition `route`; and
- literal `authorization: not-granted`.

Personal, ambiguous, denied, different-family, missing-capability and combined
capability interpretations are declined. The route is local-only, expires in
at most 30 seconds and remains `authorization: not-granted`.

The answer boundary revalidates the interpretation/route digest binding and
accepts only the fixed caller's schema-2 result, exact capability, four bounded
states, fixed source, state-appropriate check facts, bounded age and literal
non-authority. Its selected-answer record retains only the answer, fixed
capability and state; it cannot broaden the observation into a cause, repair or
general health claim.

## Validation

The focused selector suite passes **7/7** under Python 3.12.14 and Pydantic
2.13.4. The broader historical contract suite still has its previously
documented reviewed-source pin mismatch; that unrelated suite was not repinned.

This is offline composition evidence. It does not install the selector, enable
automatic routing, make a broker request, call a model or grant a capability.
The next D4 gate is a frozen synthetic answer-conformance and independent
usefulness review for the fixed Speech response.
