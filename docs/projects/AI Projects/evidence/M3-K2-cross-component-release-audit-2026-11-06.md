# M3 K2 cross-component release audit — 2026-11-06

## Outcome

The complete current K2 source boundary passes its combined offline audit at
Stream A commit `d94f2893` and platform
commit `90d99b4c`.

## Measured result

| Surface | Tests | Result |
|---|---:|---|
| Stream A K2 development, sealed evaluation, shadow, release-decision and graduation sources | 96 | pass |
| Platform development, reconciliation, session, bundle and inactive-install sources | 31 | pass |
| **Combined** | **127** | **pass** |

The Stream A discovery run covered 93 tests and the deterministic bundle
builder's separately invoked suite covered the three tests its filename does
not place under `test_nlu_k2*.py`. An initial attempt to invoke that module from
the repository root could not resolve its sibling import; rerunning from its
source directory passed 3/3 without a source change. The platform run covered
all eight current `test_m3_k2*.py` modules.

A separate broad platform regression now also passes all 52 current Lab Hours
tests. Platform commit `90d99b4c` restores the two manifest-pinned fixed-card
sources that were absent from the worktree and updates three stale tests to the
current dispatcher, 57-pin release and retired-EPUB-scheduler baseline. Both
restored source digests exactly match the pre-existing release manifest; no
installed file or active booking was changed.

## Boundary

This is source and contract integration evidence only. It did not open the
sealed evaluation, call a model, acquire a lease, start a listener or tunnel,
transfer or install the bundle, stop or restart a service, or change routing.
The already-booked 192-request development transaction and its production
restoration proof remain the next runtime gate.
