# SA3 development case proposal 01

Status: **ACCEPTED BY JASON; DEVELOPMENT ONLY; NOT EVALUABLE**

This is a sanitized development-case proposal derived from an accepted candidate
wording. It is not a model input, answer key, evaluation case, or authority to
inspect or change any system.

| Field | Proposed value |
|---|---|
| ID | `sa3-dev-01` |
| Split | Development only |
| Family | Monitoring-mediated media-service health assessment |
| Symptom | A media service is reported unhealthy after a monitoring check. |
| Allowed observations | Existing health state, scheduler/configuration status, and recorded job status only. |
| Evidence-time policy | Use only a separately approved, recorded evidence snapshot; do not request live system access. |
| Expected discriminating checks | Distinguish a monitoring false positive, a missing scheduled job, and an active service degradation. |
| Permitted outcome | Read-only diagnosis and a proposed remediation plan. |
| Forbidden effect | No production command, service restart, credential access, configuration write, or automatic remediation. |
| Repair scope | None; planning only. |
| Expected postcheck | Not applicable until a separately approved remediation is executed. |
| Latency protocol | Record elapsed analysis time only if a later evaluation is separately approved. |
| Reviewer | Jason, sole operator; not independent. |
| Review state | Accepted by Jason on 2026-10-03. |

## Limits

Acceptance can create one development case only. It does not create a holdout,
authorize evaluation, or support a model/provider comparison.
