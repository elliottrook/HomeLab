# M3 K2 guest readiness correction — 2026-11-06

## Failure found before the booking

The standard Lab Hours readiness checker returned `NO-GO` even though the
booking, dispatcher, lease and locks were healthy. The generic inactive-target
validator looked for all 12 K2 runtime pins in the Proxmox host directory.
The reviewed K2 installer correctly keeps those private runtime files inside
LXC110, so the preflight reported the first guest-only file as missing.

Without correction the dispatcher would have failed closed before the booked
workload, reproducing the prior pattern of a valid reservation that never
reached its test.

## Correction

The validator now recognizes only the registered K2 runner kind as guest-held
and checks its actual LXC110 custody through `pct exec`. It requires all 12
exact hashes, root ownership, one regular link, mode 0600 for the private
corpus/shortlist, mode 0644 for reviewed source/manifest files, and complete
`nlu_*` dependency closure. Other workload validation remains host-local and
unchanged.

The correction preserved the newer installed B60 R5 workload registration and
release pin. A two-file inactive installer verified the exact live baseline,
retained a mode-0700 rollback checkpoint, atomically replaced only
`lab_hours_workloads.py` and its release manifest, then ran registry, release
manifest and K2 guest-target proofs. No service restarted and no workload or
model effect occurred.

## Result

- focused platform tests: 40/40 pass;
- correction state: installed inactive;
- guest runtime: 12 exact files in LXC110, dependency closure complete;
- authoritative booking: still `scheduled`;
- standard readiness checker: `ready`, all nine checks true;
- dispatcher: enabled and active;
- lease: `ready`; shared locks absent;
- LXC104/110/116 and Aster Agent/accepted llama/Speech: active;
- pvescheduler/pvestatd: active;
- EPUB monitor and News ingest/digest timers: present on their fixed schedules.

This correction does not invoke K2 or authorize sealed evaluation, routing or
promotion. It removes the deterministic preflight defect that would otherwise
have prevented the approved 20:00 development transaction from starting.
