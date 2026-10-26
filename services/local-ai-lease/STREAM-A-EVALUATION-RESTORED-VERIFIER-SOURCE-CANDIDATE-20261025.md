# Stream A restored-production verifier — source candidate

Status: **SOURCE ONLY; INDEPENDENT REVIEW REQUIRED**

This no-CLI read-only verifier supplies the restoration predicate required by
the fixed F6 handlers. It has no filesystem writes and cannot restore, stop,
start or enable a service.

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/stream_a_evaluation_restored_verifier.py` | `41f54f394dd4f93d332abd6add269f9aa5ac8507b63fd2a90562e29f7358a62b` |
| `scripts/local-ai/test_stream_a_evaluation_restored_verifier.py` | `9421d324c37751fff5da908740b98ed1085e2ac3d6ff6894c9c71139d08b8bf7` |

For the exact lease identity and generation, the verifier requires:

- a unique-key restore-observer result no larger than 16 KiB and no older
  than 15 seconds;
- active, authenticated, idle accepted llama.cpp/SYCL with exactly its one
  GPU holder;
- enabled and active Aster Agent, Speech and both News timers;
- enabled and active accepted `aster-llama.service`;
- the whole-host lease state `ready`; and
- no evaluation lease, lease lock or operation lock.

The combined Stream A evaluation suite passes 78/78, including stale and
oversized observations, duplicate JSON keys, inactive consumers, foreign
whole-host lease state and residual evaluation state.

The later composition root must still compare the cycle-specific F2 schedule
snapshot, prove no evaluation child remains, and bind this verifier to the
fixed handler. No install, restoration action, F6 arm or model call is
authorized by this source candidate.
