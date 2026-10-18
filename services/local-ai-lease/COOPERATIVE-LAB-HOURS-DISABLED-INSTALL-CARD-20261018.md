# Cooperative lab-hours disabled install card

Status: source-only candidate. This card does not authorize target-Linux
installation, timer enablement, service stops, client admission, or a live
pilot.

## Candidate set

Stage exactly nine files from Stream A source commit `84cf51cd` under the
concrete target path `/usr/local/libexec/local-ai-lease/cooperative-lab/` on
the target Proxmox host (not in an LXC). The directory is root-owned mode 0700;
candidate modules are root-owned mode 0644 and tests are retained as evidence
files, not installed runtime entrypoints.

| File | SHA-256 |
|---|---|
| `cooperative_lab_session.py` | `1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260` |
| `cooperative_lab_sources.py` | `8825d1be3a695c0743e86db3da67628483e0b777a76ad920d39e55c2bfa18586` |
| `cooperative_lab_host_adapter.py` | `36b4c738c2ab665be79831833cee20f7ab0b88bddb139e7920e5bf92ffa491a9` |
| `test_cooperative_lab_session.py` | `985fd360d28930d6ae356091176c71db0e9081d0cc85b5dc2742b3b11cd737b8` |
| `test_cooperative_lab_sources.py` | `6df005816329ad8fde9c80871d5c960dbba74f542cb5980cdc3fa4ad5c28f6a6` |
| `test_cooperative_lab_host_adapter.py` | `11ded83817ad848541aced28a9f63d70fd22105f438d1682ddc3477b42b8e5ca` |
| `application_b60_lease.py` (dependency) | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| `host_exclusion.py` (dependency) | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |
| `application_b60_host_sources.py` (dependency) | `fb202b44261832672786edd07c04a94e7e4024fd9611d655d9de63755c308948` |

Tests must run with deterministic `PYTHONPATH=/usr/local/libexec/local-ai-lease/cooperative-lab`
and only this pinned directory first on the import path. Preserve the prior
checkpoint before any future replacement. Existing F2 guards and lease
controllers are outside this card and must not be overwritten.

## Disabled verification

1. Run imports and all three focused test files under target Linux.
2. Confirm no systemd unit, timer, lease state, journal, backend request or
   client-admission rule was created or enabled, and confirm the already-active
   LXC110 model listener is unchanged (address, port, process and service
   state).
3. Confirm the direct-client exclusivity check remains NO-GO until a reviewed
   MacBook client identity is configured and an exact `ss` observation proves
   every established peer matches it. Zero connections is not proof.
4. Store output and hashes as disabled-install evidence.

Any mismatch, unexpected file, failed test or ambiguous observer result stops
the install before effects. Rollback removes only the staged candidate files
and restores their exact prior checkpoint; it does not touch service state,
timers, schedules, models or network policy. If target state is uncertain,
retain the directory and lock for operator reconciliation.

## Promotion gates

Promotion requires an independently reviewed source adapter binding typed
attested envelopes to fixed Proxmox/TrueNAS/LXC observations, a trusted owner
identity and monotonic deadline wrapper, exact Linux observer output, a named
30-minute workload, and separate authorization for the daytime window. The
current MacBook path is through LXC104, which the isolation pilot stops; no
usable MacBook workload may be promoted until a lease-aware lab gateway or
equivalent admission boundary is reviewed. No reboot, fault injection or
benchmark batch is included.
