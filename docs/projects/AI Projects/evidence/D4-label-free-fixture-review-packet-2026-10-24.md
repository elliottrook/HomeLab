# D4 label-free fixture review acceptance — 2026-10-24

## Decision

Jason accepted the twelve frozen public-synthetic investigation fixtures in
`services/aster-agent/evals/sysadmin-sa3-development-fixtures-draft-v1.json`.
Acceptance makes these fixtures eligible for one separately reviewed,
tool-free development evaluation. It would not authorize a model call, B60
access, connected evidence collection, a production route, a repair, or any
promotion decision.

The file SHA-256 is
`a1d3da7d5a639489a9ecc3eace33732e12df6abc92cb37413c5dcd1be9a7a24a`. Its canonical review
SHA-256 is `59aee3a99826a75423327ab614676b31daa44f8879f4b602898ad101287ed07f`. The qualification validator binds any later review
record to that canonical digest and to the already accepted twelve-case corpus
and content-free plan. Any content change invalidates the review binding.

## Review surface

Each fixture contains only a fictional prompt, an explicit catalogue of
simulated read-only checks, one stale initial observation and current simulated
responses. The bundle is label-free: it contains no expected diagnosis, score,
answer key or repair instruction. The investigation engine can reveal at most
two simulated checks, permits at most three model calls, rejects effects and
unobserved citations, retains no private reasoning, and makes no real tool
call.

| Case | Simulated checks | Capability IDs |
| --- | ---: | --- |
| `video_archiver_jellyfin_verification` | 3 | `sanitized_retry_summary`, `media_metadata_summary`, `jellyfin_task_status` |
| `paperless_ip_collision` | 3 | `sanitized_guest_address_inventory`, `arp_result`, `netbox_ownership_result` |
| `arr_sso_header_mismatch` | 3 | `sanitized_http_status_class`, `supported_header_capability`, `sanitized_integration_health_state` |
| `doctor_report_shape_failure` | 3 | `sanitized_exit_class`, `schema_version_marker`, `count_only_finding_summary` |
| `netbox_post_reboot_startup` | 4 | `sanitized_boot_classification`, `container_health_summary`, `http_result_class`, `count_only_inventory_check` |
| `b60_software_rendering` | 3 | `sanitized_renderer_capability_summary`, `bounded_latency_band`, `service_health_state` |
| `dns_asymmetric_path` | 3 | `sanitized_route_interface_result`, `dns_response_class`, `endpoint_health_class` |
| `backup_configuration_gap` | 3 | `sanitized_coverage_state`, `backup_age_band`, `documented_recovery_dependency` |
| `backup_interruption_recovery` | 4 | `sanitized_run_state`, `last_successful_age_band`, `checkpoint_presence`, `recovery_order_reference` |
| `stale_backup_inventory` | 3 | `sanitized_document_timestamps`, `inventory_freshness_band`, `dependency_category_summary` |
| `doctor_empty_observation_set` | 3 | `sanitized_exit_state`, `item_count`, `report_schema_marker` |
| `b60_preflight_abstention` | 3 | `sanitized_preflight_outcome`, `bounded_reason_category`, `rollback_availability_marker` |

## Verification

- Bundle structural validation: PASS.
- Exact source-corpus, source-plan and per-case digest bindings: PASS.
- Model-call authority: `false`.
- Tool-call authority: `false`.
- Focused validator/investigation tests: 17/17 PASS.
- Complete evaluation suite: 135/135 PASS under Python 3.12.14 and Pydantic 2.14.1.
- Negative coverage rejects source drift, plan drift, case reordering, malformed
  simulated evidence, authority changes, missing human review and any fixture
  change after review.

## Acceptance effect

The bundle now has status `development_fixtures_reviewed` and an exact review
record naming Jason, the review date and the canonical review digest above.
Qualification validation and the complete 135-test suite pass after that
change. A model run remains a separate gate with an exact model/runtime,
request modes, timeout, output custody, scoring and abort card. Connected tools
and production Aster remain out of scope.
