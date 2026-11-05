# Lab health remediation — 2026-11-05

## Scope

Jason directed a bounded repair after HomeLab Doctor reported 74 passes, ten
warnings and six failures. This work produces no speech and creates no public
ingress, credential change, firewall expansion, backup-retention change or
remote Git write.

## Repairs

### Doctor contract reconciliation

The working branch carried the retired same-process AI-PAM approval contract,
while production had already moved to the independent approval service and
ingress. The current independent approval services, fixed diagnostic gateways
and caller sockets were healthy. Doctor now checks that deployed contract and
the exact reviewed AI-PAM catalogue. The retired approval daemon remains
disabled.

Bazarr was also healthy but deliberately bound only to the TrueNAS LAN address.
Doctor now probes `192.168.20.40:6767` instead of the unbound loopback address.

The EPUB check now reports the actual Proxmox Lab Hours scheduler and rejects a
re-enabled legacy guest timer. The scheduler remains disabled: its current
implementation only checks for an empty window and does not create the required
registered, hash-pinned workload booking or participate in the whole-host lease
and shared operation lock. No registered EPUB workload exists in the
authoritative dispatcher, so enabling the timer would violate the Lab Hours
admission contract.

### Wiki mirror

The human accepted lock had advanced while the derived mirror retained older
accepted-input metadata. A double deterministic build and verification produced
1,811 entries at content hash
`bf91c91c177cf7ac867104b91dfbf0935ab5db3bfa7235ce6732722d9e7738a2`.
The candidate was activated atomically and verifies cleanly. Corpus health now
has no failures or directory-index drift; it retains a warning for two sources
older than the freshness threshold.

Recovery copies on LXC 113:

- `/var/lib/aster-wiki/aster-knowledge-mirror.doctor-repair-20261105`
- `/var/lib/aster-wiki/aster-knowledge-mirror.pre-doctor-20261105`

### Synology configuration copy

The 04:30 TrueNAS pull raced the DSM export and copied the prior day's archive.
TrueNAS cron job 1 now runs at 04:45. Its prior task record is preserved at
`/root/doctor-repair-cron1-20261105.json`. A manual catch-up run completed, and
source and destination now match at 53,538,985 bytes and SHA-256
`61b84efd5d1d9218219a8a0481ac3ba895f3e7d73b06a4cfd5d3c42a73974493`.

### Protected exports and drift

All eight protected operator exports completed. The fresh OPNsense export
matched live `/conf/config.xml` exactly. Reviewed drift consisted only of the
documented AsterTV Home Assistant firewall rule, Bedroom reservation, LXC 116
memory increase from 4 to 5 GiB, and the Home Assistant pre-M7 snapshot record.
Arista had no change. The 88-entry baseline was accepted from the fresh exports;
the final drift check reports `NONE`.

## Validation

- 21 focused Doctor and AI-PAM tests passed.
- Shell syntax and `git diff --check` passed.
- AI-PAM and independent approval readiness passed live.
- Bazarr container, policy and LAN endpoint passed live.
- Both TrueNAS and Synology configuration checks passed.
- Wiki mirror verification passed for all 1,811 entries.
- Final Doctor: **83 passed, 6 warnings, 1 failure**.

The remaining failure is the deliberately disabled EPUB scheduler. Its next
safe action is a separate registered-workload/dispatcher integration with exact
runtime pins, booking ownership, whole-host lease, shared lock, recovery and
failure-path tests. Do not restore the older ungated guest timer.
