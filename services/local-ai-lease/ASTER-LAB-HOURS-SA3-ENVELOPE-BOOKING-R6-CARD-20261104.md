# Aster Lab Hours SA3 envelope booking r6 card — 2026-11-04

## Booking and purpose

- ID: `aster-stream-a-sa3-envelope-20261104-1500-r6`
- Owner/workload: `aster-stream-a` / `sa3-evidence-envelope-quality-v1`
- Window: 15:00–16:30 America/Vancouver, including 900-second recovery buffer
- Ledger check at 14:47: clear, no booking IDs

R6 is one fresh attempt. R3–R5 are spent and may not be retried. Its purpose is
to produce either the frozen complete 20-case/14-request result or one bounded
failure projection that identifies JSON code, traceback class, or process exit
status and channel byte counts without retaining content.

## Installed correction

- workload registry: `3bcfefd8942bbc8f31db70bce51a04ff17ce2f13adb352d816ae6cdd7237be73`;
- release manifest: `1d18a86d756e6388a72794f74f3299611234be43937c12c32159f976556d9537`;
- host adapter: `101ce58e6e103db22b9da9532528e44ac84171e178a5baeee0a4e196fe3e3c9f`;
- LXC110 wrapper: `626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`.

The inactive install passed 34 release pins, bounded JSON/class/exit-byte
projections, exact custody, ready lease, absent shared state/locks/listener,
healthy Doctor and production, and zero core restarts.

## Runtime and terminal rule

The dispatcher must recheck the exact booking, complete release pins, lease,
shared operation lock, listener absence, production health and restoration
capacity at claim. Accept success only for exactly 20 cases, 14 model requests,
zero errors/retries/effects, frozen identities, retained digest, exit zero,
`production_restored=true`, no remaining candidate state/listener/lock, lease
ready and independent production postchecks healthy.

Any other terminal state is NO-GO without retry. Retain no prompt, answer, case
identifier, traceback message or arbitrary process output. This card authorizes
no model/backend change, restart, blind-review claim, routing change, tool grant
or automatic promotion.
