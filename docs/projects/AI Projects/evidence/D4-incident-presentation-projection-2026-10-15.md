# D4 incident presentation projection — 2026-10-15

**State:** offline candidate only. No incident producer, gateway release,
AI-PAM grant or live service was changed.

The earlier SSE projection omitted `facts` and `hypotheses` but copied an
incident's free-text title and next-step reason, plus each observation's
free-text summary, source and evidence ID. Those fields can contain material
the future producer did not intend to show in the Companion. The endpoint's
current Doctor adapter uses a fixed summary, but the generic incident contract
does not guarantee that for later adapters.

The presentation now emits a fixed title, a summary built only from validated
target/kind/state, a fixed next-step reason and a one-way short reference for
the evidence ID. It omits producer source labels from this UI view. The
owner-only incident record still retains the original fields for diagnosis;
the SSE presentation schema is version 2. A synthetic marker test verifies
that all five free-text inputs stay out of the rendered payload. The focused
investigation, store, stream and Doctor adapter suite passes 23/23 tests;
`git diff --check` passes.

This narrows accidental display but is not a complete data-classification
system: future connected producers still need source-local allowlists and
secret exclusion before persistence, and public incident IDs must be generated
by the authenticated gateway. The existing `start_doctor_incident` path does
generate its own ID. Live release and the M1 authority gate remain open.
