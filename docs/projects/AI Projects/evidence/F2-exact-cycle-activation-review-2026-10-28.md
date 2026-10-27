# F2 exact-cycle activation review — 2026-10-28

**Decision:** GO for one separately approved exact-cycle activation.

Stream A reviewed platform tip
`581c5ba93d65c4af3a143e845485ded44f6b654d`, containing the fresh October 28
card and the corrected historical-unit baseline. The activation card SHA-256
is `09d59c52be301f05182a54bb92500c806ab17eaa974ad397913c44d3f5030759`;
its focused test SHA-256 is
`945a49485f07a2d82835a23048325f963b00f3baeaa4ee63978c7a984b48b320`.

## Exact candidate

| Item | SHA-256 |
|---|---|
| 01:15 preparation timer | `69d0e4d2cafed2c1567009cfa87d1146c17440a7de8ac21dce17ce76eaffa843` |
| 01:20 final timer | `b71e87d036ad70da437dba1c897b5b0f520ee4dff814af7f998522243ecd5545` |
| Installed coordinator | `efe8bc99efd95ce85d2dbe3c8218419fdb187ceaa065cf59a906e7c0323987ec` |

Target `systemd-analyze calendar` resolves the units to 01:15 and 01:20 PDT on
October 28. Read-only target validation matched all five installed source pins
with root:root mode `0644`, one-link regular-file custody. The new-cycle state,
retained receipt, lease lock and operation lock are absent; the lease is ready
and recurring F2 timers are disabled/inactive.

The initial card expected every earlier exact-date unit to be absent, but target
validation found the two preserved October 20 timer files. Their exact hashes,
root custody and disabled/inactive state match historical evidence. The corrected
card binds those two files and requires every other earlier exact-date unit to
be absent. Focused card tests pass 3/3, and the complete F2 suite passes 58 tests
with one expected non-root custody skip out of 59.

Activation remains a remote host change. It requires Jason's explicit approval
before installing/enabling only the two October 28 timers and creating the
one-occurrence 01:42 reconciliation. No service is manually started, and no F3,
lease, consumer stop, restart or model call is included. Fresh backup, task-1,
archive identity, load and quiet-host checks remain runtime gates; any failure
is terminal NO-GO without retry.
