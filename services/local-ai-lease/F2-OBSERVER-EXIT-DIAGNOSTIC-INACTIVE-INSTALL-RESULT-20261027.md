# F2 observer-exit diagnostic — inactive installation result

Status: **PASS**

Jason approved the one-file inactive installation from platform commit
`be6cafa47d77668a69181a80018a755d6f740840`.

## Installed state

| Item | Result |
|---|---|
| Predecessor SHA-256 | `6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193` |
| Installed candidate SHA-256 | `efe8bc99efd95ce85d2dbe3c8218419fdb187ceaa065cf59a906e7c0323987ec` |
| Installed custody | `root:root`, mode `0644`, one regular link |
| Rollback | `/root/aster-f2-observer-exit-rollback-be6cafa4/f2_scheduled_release_candidate.py` |
| Preserved October 27 state SHA-256 | `cf72cfbdbe8ee8c06f5848eea171e778bd3253d5dd708c67a7a691d3e94e5d2a` |

The first clean test packet omitted repository card and systemd fixtures.
Focused target tests passed 31/31, the broader suite reported only missing-file
errors, and the transaction automatically restored the exact predecessor.
Read-back verified the rollback before retry. The corrected complete packet
then passed the focused 31/31 suite, the complete 56/56 target-Linux F2 suite,
and four direct installed-path projection checks.

Recurring F2 timers remain disabled and inactive. No exact-date F2 timer is
installed, and the preserved terminal state is unchanged. No F2 or `zstd`
child, retained receipt, lease or operation lock exists. LXC104/110/116,
Aster Agent, the accepted LXC110 llama.cpp/SYCL service, Speech,
`pvescheduler` and `pvestatd` are healthy.

The installation improves evidence from a future observer failure. It does
not reconstruct the discarded October 27 child phase and authorizes no fresh
cycle, scan, F3 conversion, receipt, lease, service stop, restart, model call,
schedule change or Git push.
