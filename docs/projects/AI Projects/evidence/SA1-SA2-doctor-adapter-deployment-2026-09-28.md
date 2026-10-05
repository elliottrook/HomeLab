# SA1/SA2 Doctor adapter deployment — disabled baseline

Date: 2026-09-28
Status: **installed disabled; no connected incident pilot run**

## Delivered change

Jason authorized implementation of the narrow Doctor evidence adapter. Forgejo
`main` was published through source commit `29d0498` before installation. The
change adds a Jason-only `/v1/sysadmin/` incident boundary that can read only the
existing fixed sanitized Doctor report and present concise reconnect state.

The capability is disabled by default. No environment setting was added to enable
it, so the running service has `SYSADMIN_DOCTOR_EVIDENCE` false. The deployment
does not create a listener, timer, network path, source account or a new
credential. It cannot refresh Doctor, invoke a job, run a command, select a
target, repair a service or enable model reasoning.

## Validation

| Check | Result |
|---|---|
| Dependency-free local adapter/contract tests | 14 passed |
| Temporary staged-source test under LXC 104's existing Python runtime | 5 passed, including legacy-key denial and verified-Companion owner/reconnect behavior |
| Deployed `aster_agent.py` SHA-256 | `343bce00b777134bfb6f28f7e3218bea3a21240ed19f9cb0bad819186ab2deb0`, matching the released source |
| Service state | `aster-agent.service` active after one restart |
| Gateway availability | `GET /health` returned the normal Aster gateway health response |
| Disabled state | Executed as service user: `SYSADMIN_DOCTOR_EVIDENCE` confirmed false |

The staged runtime test initially identified a real owner-context omission for
the new route family. Commit `29d0498` adds `/v1/sysadmin/` to the existing
verified-identity middleware; the corrected staged tests passed before the
source was installed.

## Recovery and next gate

The prior gateway file is retained locally as
`/opt/aster-agent/rollback-sysadmin-doctor-20260928/aster_agent.py`. The
implementation remains inactive unless an explicit enable setting is later
deployed. Disabling/removing that setting and restarting only `aster-agent`
returns this capability to the present baseline. No rollback is needed.

Before an enabled bounded read-only pilot, obtain a separate authorization that
names the enable setting, state retention/quota, incident creation/stream
validation, 36-hour freshness test, duplicate-report behavior, observation
period and disable/rollback check. That pilot remains outside this deployment.
