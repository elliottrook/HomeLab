# Full-inference drain disabled-install card

Status: offline candidate only. This card does not authorize staging on the
Proxmox host, service stops, model starts, workload execution or reboot.

## Frozen candidate

Stage exactly these five files under the concrete target path
`/usr/local/libexec/local-ai-lease/full-inference-drain/` on the target
Proxmox host, not in an LXC. The directory is root-owned mode 0700; modules
are root-owned mode 0644. The test is evidence-only and is not a runtime
entrypoint. The source commit `7e8d259e` and hashes below must match before staging:

| File | SHA-256 |
|---|---|
| `full_inference_lab_session.py` | `372542934b068da71151d437e515445da348b06ad2c081b91d16682d953ab0b2` |
| `test_full_inference_lab_session.py` | `f45d692346d82c74f8e9f7d513e551b3071c0081a2dfa7266924155adf96e67e` |
| `cooperative_lab_session.py` | `1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260` |
| `application_b60_lease.py` | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |

Run with deterministic `PYTHONPATH` containing only this pinned directory
first. Preserve any prior checkpoint before replacement; existing F2 guards,
cooperative lab state and other lease controllers are not overwritten.

## Disabled verification and rollback

Run imports and the focused synthetic test only. Confirm that no systemd unit,
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
