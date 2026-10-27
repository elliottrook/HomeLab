# SA1/SA2 adaptive-loop regression — 2026-10-26

## Result

**PASS.** A production-dependency route test exercised the installed boundary
as one coherent loop using a temporary incident database:

1. owner-authenticated Doctor intake records the existing sanitized report;
2. a state-bound SA1 decision selects `aster-gateway/status`;
3. the registered SA2 gateway producer consumes that decision;
4. a new state-bound decision selects `inference-server/status`;
5. the registered inference producer consumes that decision;
6. reconnect reports three observations, two consumed decisions, no pending
   decision and `sufficient_or_escalate`.

The test used a fixed inference envelope so it measured route, journal and
state composition without adding a second network probe. Separate installed-
path validation already exercised the real fixed health endpoint and returned
bounded `ok` metadata.

Both private hypothesis markers were absent from the reconnect stream. A
repeated observation without a new pending decision remains denied, and the
legacy API key remains unable to enter the owner-only incident routes.

The complete LXC104 gateway test module passed **7/7** with resource warnings
fatal. The temporary test file was removed. Production services were not
restarted or changed.

## Next boundary

This closes the deterministic SA1 selection and SA2 evidence-collection loop
for two fixed sources. SA3 remains responsible for generating a useful,
bounded hypothesis/next-step proposal from the sanitized incident state. It
must not receive the private journal hypothesis history, choose an unregistered
target, execute a producer, or gain repair authority.
