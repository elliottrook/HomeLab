# D4 fixed Aster Speech caller/gateway boundary

**Date:** 2026-10-26  
**State:** source-only; not installed, registered or granted

## Fixed contract

The speech diagnostic now has a separate fixed source boundary:

- capability: `diagnostic.aster-speech.latest`;
- method: `doctor.aster-speech.latest`;
- arguments: exactly `{}`;
- evidence: only schema-3 `aster.speech` from the fixed aggregate/catalogue
  paths and configured owner;
- response: named state, UTC observation time, bounded age, deterministic
  scoped answer and `authority: not-granted`.

`fixed_speech_gateway.py` accepts only the broker UID from kernel peer
credentials and one exact request envelope. It returns no path, summary,
probe output or failure detail. `fixed_speech_caller.py` accepts only Aster's
UID, asks the broker for one 30-second request, consumes that exact request,
then independently validates the complete result before rendering it.

Changed method, arguments, envelope fields, peer identity, capability,
request ID, source, state, timestamp, age or facts fail closed. A broker outage
or unsafe result produces only the fixed unavailable error. The new capability
is distinct from `diagnostic.aster-inference.latest`; it does not reuse that
grant or widen its evidence.

## Validation

- focused speech catalogue/projection/caller/gateway tests: **22/22 passed**;
- combined new speech and existing fixed-Doctor boundary tests: **53/53
  passed**;
- Python compilation: passed.

The tests prove the exact empty request, one broker create/consume sequence,
peer denial before the broker is reached, content-free outage handling,
private/extra-field rejection and the deterministic `not-granted` result.

## Boundary and next gate

No unit, socket, identity, database row, capability registration, grant,
service restart, live read, model route or model call exists for this source
candidate.

The next milestone is a frozen additive deployment bundle with separate system
identity/socket names and disabled units. It must import against the installed
broker dependencies on target Linux and leave all files, units and sockets
inactive until a later reviewed installation. Registration, grant and any
service restart remain later effects.
