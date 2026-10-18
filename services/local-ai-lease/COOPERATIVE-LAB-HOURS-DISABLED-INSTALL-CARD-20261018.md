# Cooperative lab-hours disabled install card

Status: source-only candidate. This card does not authorize target-Linux
installation, timer enablement, service stops, client admission, or a live
pilot.

## Candidate set

Stage only the session controller, source producer, Linux observer, and their
three focused tests under a new root-owned mode-0700 private directory. Record
source commit, SHA-256, owner and mode for every staged file; preserve the
prior checkpoint before any future replacement. Existing F2 guards and lease
controllers are outside this card and must not be overwritten.

## Disabled verification

1. Run imports and all three focused test files under target Linux.
2. Confirm no systemd unit, timer, lease state, journal, model listener,
   backend request or client-admission rule was created or enabled.
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
30-minute workload, and separate authorization for the daytime window. No
reboot, fault injection or benchmark batch is included.
