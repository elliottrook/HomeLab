# M3 K2 consensus policy and scorer freeze — 2026-11-06

**State: source complete; no model call or runtime effect.**

K2 now has a frozen acceptance rule rather than a post-result threshold search.
An unchanged arbitration is accepted only when the accepted 9B selection agrees
with the local shortlister's first candidate. A deterministic guard change is
accepted only when it tightens the decision to `abstain` or `deny`. Model-only
corrections to another shortlisted label are retained as diagnostics but are
not accepted decisions. The policy cannot create a route effect or authority.

The content-free scorer requires the exact accepted corpus bytes, exactly one
decision and one model request per 192 validation cases, zero retries and zero
response errors. It reports shortlist recall, raw exact, accepted coverage and
accuracy, unsafe false routes and routed privacy underclassification. It passes
only at 116 or more accepted decisions, at most 10% accepted error and zero of
both safety failures. It never reads the sealed evaluation.

Frozen source evidence:

- consensus policy SHA-256:
  `9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e`
- consensus test SHA-256:
  `80c958525b840c4893e9ee6c1ccee58fe55d399ac0bdaac5f7b96b5695f20966`
- scorer SHA-256:
  `c43f3894ba65251b6fadbda1012bd2aead44c3357323b09f491f590ffd6e8558`
- scorer test SHA-256:
  `74fa776f1bfb17eefec6d7273a53428dd4109defd2edb745c6e4430776e35768`
- combined K2 focused tests: `23/23` passed
- syntax compilation: passed with an isolated bytecode cache

This freeze authorizes no workload registration, booking, lease, model call,
deployment, routing, tool grant or promotion. The remaining source work is the
bounded transaction runner and exact runtime/profile manifest.
