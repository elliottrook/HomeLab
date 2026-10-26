# Stream A F4/F5 admission and candidate-H inactive install card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED FOR LIVE USE**

This card replaces only the installed evaluation lease contract, adapter and
entry point, and adds the admission artifact library. It does not create F4 or
F5 evidence, acquire a lease, stop a consumer, arm a watchdog, start candidate
H or M3, call a model, alter F2, or change a schedule.

## Measured prestate

Read-only Proxmox inspection on 2026-10-25 found no evaluation lease or lock.
The evaluation watchdog and owner-heartbeat timers were disabled and inactive.
The three installed files were root-owned mode `0644` with these hashes:

| Installed path | Pre-install SHA-256 |
|---|---|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | `5c5aa6c7174d53edb775f9a2640a867634b04a9b098d0742a589a1c2dc692686` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `6876e6892cae0d81c584fee7d6f3c5b79874d9b4737d250987f451f28b6aa910` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | `0dab61905c834c36e3a865f8049c2650712422ddc27c534f1cd402b4e5ad52bb` |

## Exact candidate packet

| Source | Target | Mode | SHA-256 |
|---|---|---:|---|
| `scripts/local-ai/stream_a_evaluation_admission.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_admission.py` | 0644 | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` |
| `scripts/local-ai/evaluation_lease.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | 0644 | `3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7` |
| `scripts/local-ai/evaluation_lease_adapter.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | 0644 | `2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0` |
| `scripts/local-ai/evaluation_lease_entrypoint.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | 0644 | `d3c8924e4e1cb5165d70ca36a4fc335b465445d1881390a8ba7c83ab44a508ed` |

The existing wrapper remains unchanged at SHA-256
`15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af`.

## Contract change

The acquire intent adds exactly
`admission_receipt=stream-a-evaluation-admission-sha256:<64 lowercase hex>`.
Before `PREPARED`, the entry point opens only the fixed root-owned mode-`0600`
files under the root-owned mode-`0700` evaluation directory:

- `/var/lib/local-ai-lab/stream-a-evaluation/f5-observation.json`
- `/var/lib/local-ai-lab/stream-a-evaluation/admission.json`

Both must be canonical JSON, regular non-symlinks, one link and at most 16 KiB.
The admission is fresh for at most 15 minutes and binds the cycle, lease ID,
generation, retained backup, F2, F3, F4, F5, candidate-H digest, M3 manifest,
accepted Qwen3.5 model and accepted llama.cpp/SYCL backend. Its digest is kept
in every durable lease state. Post-quiescence rereads the same bytes, digest
and custody without incorrectly reapplying the 15-minute freshness limit.

The first workload is now `d4-candidate-h`, digest
`423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4`.
Candidate G is no longer accepted. M3 remains pinned to
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.

## Inactive transaction

1. Recheck absence of lease, lock and operation lock; require the two recovery
   timers disabled/inactive. Checkpoint the exact three installed files and
   record that the new admission library is absent.
2. Copy only the four hash-pinned files above as root-owned regular mode-`0644`
   files. Do not create either evidence artifact or any runtime state.
3. Run Python imports with `-B`, then the admission, lease, adapter, entrypoint
   and evaluation-watchdog suites. Run the unchanged wrapper without
   `--effect-authorized`; require `effects=disabled,state=source-only`.
4. Recheck no lease, lock, operation lock, F5 observation, admission artifact,
   service transition, model call, timer or schedule change occurred. Require
   the two recovery timers still disabled/inactive.

## Rollback

If any source hash, target custody, import, test or inert-wrapper check fails,
restore the three checkpointed files byte-for-byte and remove only the newly
added admission library. Re-run imports and inert checks, and retain diagnostic
evidence. Do not delete an existing or uncertain admission/F5 artifact, clear
a lease, start recovery, or touch F2. An unexpected runtime artifact or active
timer is a stop condition requiring reconciliation.

Successful inactive installation proves only source compatibility. A fresh
fixed-source F5 observation and admission production step, watchdog arming and
the effectful candidate-H/M3 run remain separate reviewed gates.
