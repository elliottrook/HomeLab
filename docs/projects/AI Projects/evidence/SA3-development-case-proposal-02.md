# SA3 development case proposal 02

Status: **ACCEPTED BY JASON; DEVELOPMENT ONLY; NOT EVALUABLE**

| Field | Proposed value |
|---|---|
| ID | `sa3-dev-02` |
| Split | Development only |
| Family | Web-application reachability after a network identity change |
| Symptom | A web application becomes inaccessible after a network identity change. |
| Allowed observations | Recorded address-management state, service health state, and approved access-test results only. |
| Evidence-time policy | Use only a separately approved, recorded evidence snapshot; do not request live access. |
| Expected discriminating checks | Distinguish an address conflict, service unavailability, an access-control denial, and an outdated client route. |
| Permitted outcome | Read-only diagnosis and a bounded recovery plan. |
| Forbidden effect | No network change, firewall change, service restart, credential access, configuration write, or automatic remediation. |
| Repair scope | None; planning only. |
| Expected postcheck | Not applicable until separately approved remediation. |
| Latency protocol | Record elapsed analysis time only if a later evaluation is separately approved. |
| Reviewer | Jason, sole operator; not independent. |
| Review state | Accepted by Jason on 2026-10-03. |

This proposal is not a model input, answer key, evaluation case, or authority to
inspect or change a system.
