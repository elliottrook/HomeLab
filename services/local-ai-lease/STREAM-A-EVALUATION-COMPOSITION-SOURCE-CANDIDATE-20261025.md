# Stream A evaluation composition source candidate

Status: **SOURCE-ONLY; INDEPENDENT REVIEW GO**

This candidate closes the remaining source composition gaps for the future
D4 candidate-H plus M3 evaluation. It is not installed, has no executable
host CLI, and does not authorize or perform F2/F3/F4/F5 production, recovery
arming, a lease, consumer isolation, a model call, cleanup, or Git push.

## Exact source packet

| File | SHA-256 |
|---|---|
| `scripts/local-ai/stream_a_evaluation_evidence_loader.py` | `836f627cd2702dffd59c77b77adab2aded01805ee43553a11471cfddfeb80a01` |
| `scripts/local-ai/stream_a_evaluation_guest_outcome.py` | `027183c9f10923cc4aa3053934b5f090d8e01f86aa81c9730d93abc143e6dcb9` |
| `scripts/local-ai/stream_a_evaluation_host_outcome.py` | `6b986fb71dca8657aa56b9fe8ef904223445e64b4122a827324adaf300c64321` |
| `scripts/local-ai/stream_a_evaluation_outcome_verifier.py` | `9408623489d52f7923c8dcca246159bb13a7926aa0a820c765fc8f3a339b58e1` |
| `scripts/local-ai/stream_a_evaluation_restore_observer.py` | `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2` |
| `scripts/local-ai/stream_a_evaluation_restored_verifier.py` | `a83de6bcdf0b275b9f238acda1a35e7518eae12f47eb220faf8f822d9a5e0d93` |
| `scripts/local-ai/stream_a_evaluation_runtime.py` | `7cda2842afa25bfca9cb47e30f433474c440ccf18123c80e7c55b54c66eb7210` |

The six corresponding `test_stream_a_evaluation_*.py` files are part of the
review packet. Their hashes are recorded by the candidate commit rather than
duplicated here.

## Fixed boundaries

The evidence loader opens only the fixed root-owned mode-`0600`, one-link
F2/F3/F4/F5/admission files below mode-`0700` parents. It requires unique-key
canonical JSON and bounded sizes. It independently revalidates the current
cycle F2 terminal success, re-resolves and re-stats the retained F3 archives,
requires exact row-for-row F2/F3 archive identity and timing agreement,
checks the fresh F4 lease/generation/backup binding, and then checks the exact
F5/admission digest graph. It returns only `AcceptedEvidence`.

The guest verifier opens D4 and M3 private artifacts inside LXC104 and LXC110
under their fixed owners and modes. Successful output contains only schema,
workload name, journal digest, result digest and call count. The host boundary
uses fixed `pct exec` commands, rejects stderr, foreign names, duplicate keys,
oversized output and call-count drift, and adds only the host-measured elapsed
time. Direct guest invocation is inert unless the fixed host command supplies
`--verify-authorized`; the gate permits verification only and cannot start a
workload or model request.

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

`stream_a_evaluation_runtime.py` is the single composition root. Its public builder
loads evidence before wiring the fixed plan, guest outcome verifier,
restoration verifier, handlers and identity-path effect driver. The returned
builder exposes no command runner, path, UID, clock, sleep or component
override; those production identities are hard-wired. The returned `run()`
method is effectful, but there is deliberately no CLI or installed
wrapper capable of invoking it in this source candidate.

## Validation

On macOS, the complete focused pattern passed **95/95** after the guest
dependency-closure correction:

```text
PYTHONPATH=scripts/local-ai PYTHONPYCACHEPREFIX=/private/tmp/pycache-stream-a \
  python3 -m unittest discover -s scripts/local-ai \
  -p 'test_stream_a_evaluation*.py'
```

The remaining gates are independent source review, target-Linux import/tests,
an exact inactive installation packet with rollback, a fresh same-cycle
F2/F3/F4/F5 admission preflight, and a separately approved supervised live
run. No model or tool promotion follows automatically from an evaluation.

Independent review accepted the corrected F2/F3 cross-binding and hard-wired
composition root at `00c975eb`, then separately accepted the inert guest
verification gate at `85c30e44`. No source-review defect remains open.

The later target inventory found that the two-file guest packet still imported
the host-only `evaluation_lease.py` module. The verifier now carries only the
two immutable release identities it needs, while a source test cross-checks
them against the host lease contract. An isolated two-file run with an empty
`PYTHONPATH` returns the canonical disabled result and writes no bytecode.
The correction is committed at `37452660`; the clean-commit archive passed
95/95 tests on Proxmox and the isolated two-file check passed in both target
guests before any installation was attempted.
