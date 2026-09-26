# M1 `a5e8b22` supersession map

Date: 2026-09-25. This records how the earlier all-at-once M1 candidate was
reconciled after the approved Stage1 split. Commit `a5e8b22` remains immutable
history; its active probe/test entry points are not the deployed design.

| Earlier requirement or artifact | Current disposition |
|---|---|
| Authenticated originating-agent binding | Deployed Stage1 core and transport; covered by `test_adaptive_foundation_regressions.py` and broker socket denial tests |
| Current-policy digest and legacy unbound denial | Deployed Stage1; covered by policy drift, policy-version, legacy migration and safe-write pre-gateway denial tests |
| Concurrent consume/revoke/approve and restart durability | Deployed Stage1; covered by multi-connection consumption, approval/revocation, restart, expiry and isolated-restore tests |
| Process exit before/after commit | Ported to the active Stage1 regression suite using Green synthetic requests, without the undeployed approver database |
| SQLite lock timeout | Ported to the active Stage1 regression suite; a blocked writer leaves the request approved and permits one later consume |
| Agent/service change and restore | Active tests prove demotion/promotion and service disable/enable revoke without resurrection |
| No-op policy update | Active test proves same-state/same-enabled updates preserve a valid request |
| Direct grant/capability mutation and restoration | Open Stage2/management gate. Stage1 exposes no grant-removal or capability-edit socket/API. Raw database edits are unsupported administration and can reproduce a prior policy digest; any future supported mutator must revoke affected requests atomically and add a regression before deployment |
| DB `set_approver_enabled` design and `approver-enable`/`approver-disable` commands | Superseded and removed from active code. They target an undeployed schema/API. The reviewed Stage2 candidate uses explicit configuration allowlists and verified claim-to-assurance mapping instead |
| `test_adaptive_lifecycle.py` and `check_adaptive_migration.py` | Removed from active discovery after their applicable Stage1 requirements were mapped/ported above. Their exact source remains recoverable at `a5e8b22` |

The authoritative deployed evidence is
[`M1-stage1-deployment.md`](M1-stage1-deployment.md). Stage2 remains undeployed;
this map does not authorize it or close its identity/assurance gates.
