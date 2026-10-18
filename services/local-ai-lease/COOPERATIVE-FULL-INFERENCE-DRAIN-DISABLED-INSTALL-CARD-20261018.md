# Full-inference drain disabled-install card

Status: offline candidate only. This card does not authorize staging on the
Proxmox host, service stops, model starts, workload execution or reboot.

## Frozen candidate

Stage exactly fourteen files under the concrete target path
`/usr/local/libexec/local-ai-lease/full-inference-drain/` on the target
Proxmox host, not in an LXC. The directory is root-owned mode 0700; modules
are root-owned mode 0644. The test is evidence-only and is not a runtime
entrypoint. The source commit `a6cbbec8` containing the final source/validator
packet and the hashes below must match before staging:

| File | SHA-256 |
|---|---|
| `full_inference_lab_session.py` | `104d6bdfa2296abfe026d0017ab935ca2351519fab84116b073e11afb3c6301d` |
| `test_full_inference_lab_session.py` | `8d2d07119dd12f0f6c61a4cf4f7d679a445f60f8959170b759a78c7666470624` |
| `cooperative_lab_session.py` | `1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260` |
| `cooperative_lab_host_adapter.py` | `720a2c9ac9fb278223e31c998fe58af234d84451344daa63dabcf55b2ebd98a6` |
| `test_cooperative_lab_host_adapter.py` | `e9433ab5b35dc11881f0a5416e5c8cd94243919b5b7264e9ccf629bffbf73b7a` |
| `full_inference_lab_sources.py` | `1f53e61b6909c26b6658d17396eff9babb4f2253b470fe33d8b188bfc9980c39` |
| `full_inference_lab_validator.py` | `5cf1562a98c7a01528c5e3f2e2d80c69c5805f0e9dc4fceec1916d15d0d686f4` |
| `full_inference_lab_runtime.py` | `1a9898dde72399f435ed93f88322be53675dd2ac49a0aeb20495a9781ad80848` |
| `full_inference_lab_install_preflight.py` | `7f725f00bf3aa62bfac7697575e5b5735a5186e915e98cddac0ebfe5adca1e06` |
| `test_full_inference_lab_sources.py` | `eab6fb2fc1bc7aa0dd14ee001aee7a58bafb73faf5b3c0f0adb52b31e5be8650` |
| `test_full_inference_lab_validator.py` | `b3806c9e769dbcf77efe23d616147365961087c91e7cd6413e3e7cb8c6341f91` |
| `test_full_inference_lab_install_preflight.py` | `fc5425aff28517ab5e29cfd562bb4af01dbd7be620022ef928fc123be1da7a1d` |
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
