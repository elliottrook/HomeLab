# F2 exact-cycle activation result — 2026-10-22

## Result

**ACTIVATED for one conditional, supervised read-only cycle. F2 remains open
until terminal evidence is reconciled.**

Jason approved the [reviewed candidate](F2-exact-cycle-activation-review-2026-10-22.md).
Only the two date-specific, nonpersistent timer units from platform commit
`f239d097` were installed and armed.

| Timer | Installed SHA-256 | Next firing |
|---|---|---|
| `f2-preflight-prepare-20261022.timer` | `8abd7ddb82fbedb38d72c10957998b6f533f09155dc4fa6e2fd56a0fc605f9a0` | 2026-10-22 01:15 PDT |
| `f2-preflight-final-20261022.timer` | `ef38ebc9d2fe761498813ab8c2c1182c3283eb7ba46f23577f78fb287bf1ee6d` | 2026-10-22 01:20 PDT |

Target-side `systemd-analyze verify` accepted both units. Calendar validation
resolved the intended Vancouver times to 08:15 and 08:20 UTC. Both units are
enabled and active; neither service was manually started.

## Activation gates

Immediately before activation:

- the coordinator and all four corrected dependency hashes matched;
- whole-host lease state was `ready` with no lease or lock;
- no October 22 F2 state or archive-integrity receipt existed; and
- recurring F2 timers were disabled and inactive.

The approved one-time observation-only reconciliation is active for 01:42
Vancouver. It may read terminal evidence and remove/disable the spent date
units. It may not invoke or retry the scan, write an F3 receipt, acquire a
lease, stop a service, run A1 or call a model.

## Pass and failure semantics

Any missing, failed, late, drifting, competing or uncertain prerequisite
means NO-GO without a retry. F2 is complete only if the root-custodied terminal
state contains exactly three valid current-cycle archive rows with exit zero
inside all bounds and clean postchecks. Timer activation alone is not evidence
of backup integrity and cannot advance F3.
