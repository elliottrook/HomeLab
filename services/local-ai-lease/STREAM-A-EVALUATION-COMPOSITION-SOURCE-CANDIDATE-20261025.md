# Stream A evaluation composition source candidate

Status: **SOURCE-ONLY; INDEPENDENT REVIEW REQUIRED**

This candidate closes the remaining source composition gaps for the future
D4 candidate-H plus M3 evaluation. It is not installed, has no executable
host CLI, and does not authorize or perform F2/F3/F4/F5 production, recovery
arming, a lease, consumer isolation, a model call, cleanup, or Git push.

## Exact source packet

| File | SHA-256 |
|---|---|
| `scripts/local-ai/stream_a_evaluation_evidence_loader.py` | `9a9792ed45194e0fdc16c7f5dfd90d77b5893d1fda3beddec1de6c40573a4125` |
| `scripts/local-ai/stream_a_evaluation_guest_outcome.py` | `bc00a8997e5d6f0ad8355ee0cc580c91d14ef3bf65cff007bdc6ca50ebb0e1e9` |
| `scripts/local-ai/stream_a_evaluation_host_outcome.py` | `81e90c4c038f0d8f134cb19b83d1e7ccdf371ba2d5f2ff9bd2a08d7371007ff2` |
| `scripts/local-ai/stream_a_evaluation_restore_observer.py` | `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2` |
| `scripts/local-ai/stream_a_evaluation_restored_verifier.py` | `a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93` |
| `scripts/local-ai/stream_a_evaluation_runtime.py` | `b4ea461c93ddd5c8b46e3821bd3d8457d99b864a748160b5d935cb3ba9ca2b1d` |

The six corresponding `test_stream_a_evaluation_*.py` files are part of the
review packet. Their hashes are recorded by the candidate commit rather than
duplicated here.

## Fixed boundaries

The evidence loader opens only the fixed root-owned mode-`0600`, one-link
F2/F3/F4/F5/admission files below mode-`0700` parents. It requires unique-key
canonical JSON and bounded sizes. It independently revalidates the current
cycle F2 terminal success, re-resolves and re-stats the retained F3 archives,
checks the fresh F4 lease/generation/backup binding, and then checks the exact
F5/admission digest graph. It returns only `AcceptedEvidence`.

The guest verifier opens D4 and M3 private artifacts inside LXC104 and LXC110
under their fixed owners and modes. Successful output contains only schema,
workload name, journal digest, result digest and call count. The host boundary
uses fixed `pct exec` commands, rejects stderr, foreign names, duplicate keys,
oversized output and call-count drift, and adds only the host-measured elapsed
time.

The restored observer now additionally requires:

- recurring F2 timers disabled and inactive;
- the spent cycle-specific F2 timers absent and inactive;
- the D4 systemd workload inactive;
- no exact M3 runner process;
- the previously required accepted llama.cpp/SYCL service, authentication,
  idle endpoint and sole accepted GPU holder.

The restored verifier binds those facts to the lease cycle and continues to
require the four production consumers enabled/active, the whole-host lease
exactly ready, and no evaluation state or locks.

`stream_a_evaluation_runtime.py` is the single composition root. Its builder
loads evidence before wiring the fixed plan, guest outcome verifier,
restoration verifier, handlers and identity-path effect driver. The returned
`run()` method is effectful, but there is deliberately no CLI or installed
wrapper capable of invoking it in this source candidate.

## Validation

On macOS, the complete focused pattern passed **92/92**:

```text
PYTHONPATH=scripts/local-ai PYTHONPYCACHEPREFIX=/private/tmp/pycache-stream-a \
  python3 -m unittest discover -s scripts/local-ai \
  -p 'test_stream_a_evaluation*.py'
```

The remaining gates are independent source review, target-Linux import/tests,
an exact inactive installation packet with rollback, a fresh same-cycle
F2/F3/F4/F5 admission preflight, and a separately approved supervised live
run. No model or tool promotion follows automatically from an evaluation.
