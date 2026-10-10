# Proposed first connected SA1/SA2 producer: sanitized Doctor status

Date: 2026-09-28
Status: **reviewed proposal only; not installed, enabled or deployed**

## Why this is the first candidate

It reuses the existing bounded health-report path instead of granting Aster a
new network credential or general diagnostic identity. The source is already
sanitized at collection time and the gateway already consumes it read-only for
the ordinary Lab Health response. The proposed producer only translates that
same trusted handoff into one typed incident observation; it does not collect,
refresh, restart or repair anything.

## Observed current boundary

Read-only inspection on 2026-09-28 established:

| Layer | Current state | Proposed use |
|---|---|---|
| Source schedule | macOS LaunchAgent `ca.yampy.homelab-report`, configured from Jason's account and running `scripts/scheduled-report.sh` daily at 08:15 | Remains the sole collector; no Aster-triggered refresh |
| Source transformation | `build-aster-health-report.py` parses only Doctor pass/warn/fail lines, selects at most 32 checks and writes the aggregate `schema`, `generated_at`, `status`, `checks` report | Retain its sanitization; do not pass raw Doctor output onward |
| Transport | Existing fixed publish uses the Proxmox route and atomically replaces LXC 104's fixed health JSON | Reuse only this established fixed handoff; no user/model target parameters |
| Handoff | `/var/lib/aster/health/latest.json` is regular `root:aster`, mode `0640`; directory is `root:aster`, mode `0750` | Read-only source for one adapter |
| Consumer | `aster-agent.service` runs as `aster:aster` with `ProtectSystem=strict`, `NoNewPrivileges=yes`, and an explicit read-only health path | Keep this identity and sandbox; the adapter runs in-process with no write/network capability |

The observed report currently has exactly `checks`, `generated_at`, `schema` and
`status`; its latest inspection found 32 checks. The established consumer code
already bounds individual names and summaries before using the report. No report
finding, raw Doctor line or credential was copied into this proposal.

## Proposed narrow bridge

Add an opt-in `homelab-doctor-report/v1` adapter inside the existing Aster
process. It reads only the fixed report path and accepts only its exact current
four-field report schema. For a newly opened incident that plans
`homelab-doctor/status`, it emits at most one envelope per report generation:

```json
{
  "schema_version": 1,
  "producer": "homelab-doctor-report/v1",
  "produced_at": "<report generated_at>",
  "observation": {
    "evidence_id": "doctor-<digest-prefix>",
    "incident_id": "<server-generated incident id>",
    "target": "homelab-doctor",
    "kind": "status",
    "observed_at": "<report generated_at>",
    "state": "ok|warn|fail|unavailable",
    "summary": "bounded aggregate status only",
    "facts": {"check_count": 0},
    "truncated": false
  }
}
```

`state` maps `healthy` to `ok`, `warning` to `warn`, and `failed` to `fail`.
Malformed, missing, future-dated or older-than-36-hours reports produce a local
`unavailable` observation. They never cause a source refresh, a network request,
a model retry or an inferred healthy state. The digest is of the sanitized report
bytes only and is used only to deduplicate the same generation; no raw report
must be logged or presented.

The UI/presentation bridge may expose the source, age, aggregate state, check
count, bounded summary and truncation flag. It must retain the existing rule to
withhold raw facts, prompts, hypotheses and reasoning from the stream.

## Controls, retention and rollback

The proposed configuration is an explicit opt-in disabled by default, for
example `ASTER_SYSADMIN_DOCTOR_EVIDENCE=0`. Enabling it creates no new listener,
timer, credential, network path, service account, write path or Lab Operations
authority. Disabling it immediately makes the adapter unavailable and leaves the
existing Lab Health tool unchanged. Removing the source file restores the
current accepted advisor behavior.

Persist only the existing local incident record: generated time, source label,
aggregate state, check count, bounded summary, age, truncation and dedup digest.
Retain no raw Doctor output, credentials, prompts or model reasoning. Retention
duration, state-directory quota and backup inclusion must be fixed in the
deployment change before enablement; they are not inferred here.

## Required deployment gate

This proposal is ready for a small connected read-only pilot only after Jason
authorizes a named change that includes: the exact default-disabled configuration,
adapter code and tests; state-directory ownership/mode; 36-hour freshness test;
rate/dedup behavior; one disabled-path test; and rollback by disabling the
adapter and restarting only `aster-agent`. The pilot must begin with the adapter
disabled, prove that existing Lab Health behavior is unchanged, then enable it
for a bounded observation period. It cannot authorize Qwen reasoning, a new
model, direct Mac/Proxmox access, repair execution or any other target.
