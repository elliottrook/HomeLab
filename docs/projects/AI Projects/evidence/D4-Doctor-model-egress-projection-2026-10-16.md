# D4 Doctor model-egress projection — offline candidate

**Status:** source-only; no gateway import, connected Codex tool, model call or AI-PAM grant.

The local incident record retains a producer summary and facts for audit. Its
generic validation rejects secret-like *field names* but cannot establish that
a summary or fact value is safe to send to a model. The new
`doctor_model_projection.py` is an explicit, separate egress boundary for the
two existing Doctor producers. It accepts only registered Doctor `status`
observations no older than 36 hours, rejects truncated or unexpected shapes,
and constructs a fixed result from the state, timestamp and typed producer
facts. It does not copy the producer summary or report digest. An unavailable
aggregate exposes only a registered reason class; an unavailable structured
check exposes no facts. Other targets and producers fail closed.

The focused projection/Doctor/investigation suite passed 24 tests, including
an actual aggregate adapter output with a private-text fixture in the report,
extra facts, malformed counts, unregistered producers and stale evidence.
The fixture marker was absent from the projected value. This is a narrow
privacy-contract check, not proof that every future producer is safe.

The projection does not authenticate producer origin on its own: a live
connection would have to bind an approved read-only adapter, fixed report
path, process identity and AI-PAM authority outside model control. It also
does not establish diagnostic usefulness compared with the existing Aster
health answer path. Those M1 and blinded-usefulness gates remain open; no
schema 2 promotion follows from these tests.
