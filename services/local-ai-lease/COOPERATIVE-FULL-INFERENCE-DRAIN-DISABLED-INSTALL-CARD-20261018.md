# Full-inference drain disabled-install card

Status: offline candidate only. This card does not authorize staging on the
Proxmox host, service stops, model starts, workload execution or reboot.

## Frozen candidate

Stage exactly fourteen files under the concrete target path
`/usr/local/libexec/local-ai-lease/full-inference-drain/` on the target
Proxmox host, not in an LXC. The directory is root-owned mode 0700; modules
are root-owned mode 0644. The test is evidence-only and is not a runtime
entrypoint. The source commit `455d1132` containing the final source/validator
packet and the hashes below must match before staging:

| File | SHA-256 |
|---|---|
| `full_inference_lab_session.py` | `d6bee982522696603924969dfcfd1a9e8303f6a5b3148f9e8158add4141a6c77` |
| `test_full_inference_lab_session.py` | `2e163db3eeb9ba53f10e78c54e33dafc90f378fba0408764fe36a0eb95effa89` |
| `cooperative_lab_session.py` | `1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260` |
| `cooperative_lab_host_adapter.py` | `0f49cca4a08aa56a2c1178820d55d2ee6f3050e794f232a7a7b94658f0f358b7` |
| `test_cooperative_lab_host_adapter.py` | `e9433ab5b35dc11881f0a5416e5c8cd94243919b5b7264e9ccf629bffbf73b7a` |
| `full_inference_lab_sources.py` | `9285066669b4a943791d6c51758548f67c8db4e20643c7cb14f4ca0b06257604` |
| `full_inference_lab_validator.py` | `59cde81f3011243c227d7c5d170524eaf7436dfeabe4a6d710103a54aad5ff88` |
| `full_inference_lab_runtime.py` | `8beab54e617853a73908108aba6207e47dfcc4546e13a6275790ce87bffd249b` |
| `full_inference_lab_install_preflight.py` | `72ab5857e1a964f4d831ea923957356d3ce5799ae0e3cc1dc2a3c9cf82d2388e` |
| `test_full_inference_lab_sources.py` | `b18f8fb711d369f7a9b7b83edfbdeaae220d6b1f1247d756346f4def761f95ed` |
| `test_full_inference_lab_validator.py` | `e89c516e6190ab69936bbe4544d5a75aa0742410db160ddc9e592108485da7dd` |
| `test_full_inference_lab_install_preflight.py` | `2e6eb97b8521ba782ce3914970ff5b7dd3414d70049525451b2862b6d38eee5d` |
| `application_b60_lease.py` | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |

Run with deterministic `PYTHONPATH` containing only this pinned directory
first. Preserve any prior checkpoint before replacement; existing F2 guards,
cooperative lab state and other lease controllers are not overwritten.

## Disabled verification and rollback

Run `full_inference_lab_install_preflight.validate_imports()` and all focused
synthetic test files only. Confirm that no systemd unit,
timer, lease state, journal, backend process, model request, workload or
network rule was created. Confirm the existing LXC110 listener/service state
is unchanged. A failure or hash/mode/owner mismatch stops before effects.

Rollback removes only these staged candidate files and restores their exact
prior checkpoint. It must not stop or start any guest, alter schedules, alter
GPU binding, touch VM105, or run the queued accepted-9B control. Uncertain
state retains the directory and lock for operator reconciliation.

## Promotion gates

The first live 30+15 run is isolation/recovery only and attended throughout.
It must not be installed as an unattended recurring controller; owner loss
retains the lock for supervised `resume_existing` or manual reconciliation. A
later usable run needs
the named queued accepted-9B control, a fresh source-bound baseline, verified
MacBook operator/admin path, and explicit confirmation that restored SYCL/GPU,
model, service and schedule state matches the accepted baseline. F2/F3 remain
separate gates; no reboot or fault injection is part of this lane.
