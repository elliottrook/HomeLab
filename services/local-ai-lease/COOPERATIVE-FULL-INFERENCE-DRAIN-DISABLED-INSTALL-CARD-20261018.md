# Full-inference drain disabled-install card

Status: offline candidate only. This card does not authorize staging on the
Proxmox host, service stops, model starts, workload execution or reboot.

## Frozen candidate

Stage exactly seven files under the concrete target path
`/usr/local/libexec/local-ai-lease/full-inference-drain/` on the target
Proxmox host, not in an LXC. The directory is root-owned mode 0700; modules
are root-owned mode 0644. The test is evidence-only and is not a runtime
entrypoint. The source commit containing the final controller/observer fix and
the hashes below must match before staging:

| File | SHA-256 |
|---|---|
| `full_inference_lab_session.py` | `ba56b832c47cda20dde9716b77522ada0a4829c3c4f5a5543f01d8f4ac0f7992` |
| `test_full_inference_lab_session.py` | `1a47dad9da6855c946ec7514c3853355014c4d5f3fc417d9b5128f676dcdbd20` |
| `cooperative_lab_session.py` | `1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260` |
| `cooperative_lab_host_adapter.py` | `0f49cca4a08aa56a2c1178820d55d2ee6f3050e794f232a7a7b94658f0f358b7` |
| `test_cooperative_lab_host_adapter.py` | `e9433ab5b35dc11881f0a5416e5c8cd94243919b5b7264e9ccf629bffbf73b7a` |
| `application_b60_lease.py` | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |

Run with deterministic `PYTHONPATH` containing only this pinned directory
first. Preserve any prior checkpoint before replacement; existing F2 guards,
cooperative lab state and other lease controllers are not overwritten.

## Disabled verification and rollback

Run imports and both focused synthetic test files only. Confirm that no systemd unit,
timer, lease state, journal, backend process, model request, workload or
network rule was created. Confirm the existing LXC110 listener/service state
is unchanged. A failure or hash/mode/owner mismatch stops before effects.

Rollback removes only these staged candidate files and restores their exact
prior checkpoint. It must not stop or start any guest, alter schedules, alter
GPU binding, touch VM105, or run the queued accepted-9B control. Uncertain
state retains the directory and lock for operator reconciliation.

## Promotion gates

The first live 30+15 run is isolation/recovery only. A later usable run needs
the named queued accepted-9B control, a fresh source-bound baseline, verified
MacBook operator/admin path, and explicit confirmation that restored SYCL/GPU,
model, service and schedule state matches the accepted baseline. F2/F3 remain
separate gates; no reboot or fault injection is part of this lane.
