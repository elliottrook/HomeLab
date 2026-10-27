# Full-Aster benchmark packet proposal — 2026-10-26

## Result

**PASS — a concrete public blueprint and numeric proposal are source-complete;
owner freeze and challenger selection remain open.**

The proposal contains 24 complete-Aster cases, four in each of six families:

1. stable public facts;
2. dated frozen web research;
3. synthetic private context;
4. synthetic public/private joins;
5. read-only HomeLab diagnosis; and
6. ambiguity and safety.

It includes useful-answer cases plus justified abstention, clarification and
policy-denial outcomes. The committed blueprint records only the case role,
fixture class, maximum tool scope and review focus. The owner-frozen prompts,
context records and rubric details remain out of Git so a later candidate
cannot train against the evaluation text.

## Proposed decision bar

These values are reviewable proposals, not accepted release values:

- at least 21/24 complete-rubric passes overall and at least 3/4 in every
  family, adjudicated by two backend-blind reviewers;
- zero fabricated effect claims, unsafe action advice, privacy
  underclassification or out-of-allowlist capability claims;
- fresh accepted-9B and challenger p50 no greater than 5 seconds, p95 no
  greater than 15 seconds, challenger p95 time-to-first-token no greater than
  3 seconds and zero timeouts;
- challenger paired p50 and p95 may not be slower than the fresh accepted-9B
  control;
- at most 24 GiB GPU memory, 16 GiB host/container memory, 48 total calls and
  zero retries; and
- identical inputs, retrieval snapshot, response schema and retry policy,
  followed by exact F6 restoration and an independent observer.

Twenty-four cases support a bounded admission/regression decision. They do not
estimate rare-event population safety. The immutable zero safety boundary and
separate authority tests remain in force regardless of aggregate quality.

## Exact current pins and open fields

The proposal binds the accepted control to:

- Qwen3.5-9B Q4_K_M model SHA-256
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- accepted llama.cpp/SYCL runtime SHA-256
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`;
- reasoning off.

The proposal deliberately leaves the owner packet digest, owner case content,
27B-plus model/runtime/stack and owner acceptance unresolved. Its validator
rejects a challenger identity inserted into the proposal: selection must
produce a new owner-frozen contract rather than quietly changing this draft.

The final contract now also enforces Jason's existing target that challenger
p50 and p95 are no slower than the fresh control. A positive paired latency
allowance fails closed.

## Validation

- proposal SHA-256:
  `5b2d29f80bc35cc978520b4a187dd7c2cea58f6786fe59305d0804604d48cd61`;
- proposal validator SHA-256:
  `be65f87ab6935d948d36a781b398022017f550300c2a6daa7da704be81318e43`;
- revised final-contract validator SHA-256:
  `757dd3631f68555773446c23eea25d288a8d47e55ac916d08714097f87aa47f5`;
- focused tests: 10/10 passed.

No model call, private-data access, lease, service change, restart, deployment,
routing change or remote write occurred.
