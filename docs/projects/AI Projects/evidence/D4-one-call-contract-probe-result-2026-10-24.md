# D4 one-call contract probe result — 2026-10-24

## Result

The explicitly approved probe at digest
`04774564801ebc0f21347d44fbdec53cbca7555bb0b90b70dff7859eee779873`
ran exactly once on the accepted Qwen3.5-9B Q4_K_M / llama.cpp b11429 /
SYCL service.

- The response was valid JSON and an object.
- The closed answer-shape result was `duplicate_evidence_id`.
- The semantic status was `invalid_answer:duplicate_evidence_id`.
- The request completed with `finish_reason=stop` in 2.700 seconds using 118
  completion tokens.
- There was no reasoning output or tool call.
- No model text, reasoning, credential, prompt or fixture content was retained.
- The postcheck was idle and healthy; the service stayed active/running with
  zero restarts and the lease returned `ready`.

The owner-only result remains at
`/root/aster-d4-development-evidence-20261024/contract-probe-04774564.json`
in LXC104, mode 0600, SHA-256
`bce7940cd502a231e709d602cfac9ecd88ad3ea569b3dbe84ba7ceee5b463507`.
Temporary source packages were removed after capture.

## Measured correction

The accepted llama.cpp path did not enforce the request schema's
`uniqueItems` constraint for `evidence_ids`. Duplicate citations do not add an
authority, observation or claim; evidence identity is set-valued. The offline
candidate therefore:

1. keeps `uniqueItems` and explicitly tells the model to list each ID once;
2. validates that every citation is a string;
3. canonicalizes repeated citations in first-seen order;
4. records only the count removed as content-free metadata; and
5. retains the independent observed-evidence subset check after
   canonicalization.

Tests prove that duplicate observed IDs are accepted once while a duplicated
unobserved ID remains rejected. The complete evaluation suite passes 148/148.
The resulting exact twelve-case run digest is
`9a089af8bf599bfbea35bc1ead7ea70d93c52f6345c7aeee2d40d77c118b2078`.
It requires separate execution approval and cannot inherit the probe approval.
