# SA1/SA2 offline candidate — typed incident evidence

Date: 2026-09-28
Status: **local implementation candidate; not deployed or connected**

## Purpose

`services/aster-agent/sysadmin_investigation.py` is the first controlled
implementation step after SA0. It creates a bounded incident record that can
accept only sanitized observations produced by a future registered adapter.
It has no network, subprocess, filesystem-discovery, credential or job-execution
code. It cannot contact a target, issue a command, call Lab Operations or claim
a repair succeeded.

The component addresses the missing structural pieces identified in the live
diagnostics: a single preloaded context was insufficient for multi-stage
diagnosis, and the agent had no durable, provenance-bearing incident state.

## Contract

An incident contains a title, up to four planned read-only observations, up to
three hypothesis summaries and the received evidence. Each evidence record
requires a stable identifier, incident binding, registered target and kind,
UTC observation time, producer/source label, state, bounded summary, bounded
sanitized facts and an explicit truncation flag. The persisted/public form adds
calculated age in seconds.

The initial catalogue is deliberately small:

| Target | Allowed evidence |
|---|---|
| Aster gateway | status, log, config |
| Inference server | status, log, config |
| Forgejo main | git |
| HomeLab Doctor | status, network |
| Backup catalogue | backup |

Unknown target/kind pairs, duplicate evidence IDs, another incident's evidence,
future timestamps, oversized facts and secret-shaped field names fail closed.
An unavailable or truncated observation remains evidence; it does not become a
success claim. The loop returns only the next **proposed read-only** observation
and explicitly states that it has not executed it.

## Validation

`python3 -m unittest test_sysadmin_investigation.py` passes five tests. They
cover provenance/age, the next proposed observation, unregistered or
cross-incident evidence, future timestamps, nested secret-shaped fields,
truncation/unavailability, and incident/hypothesis bounds. These are local
contract tests, not a Qwen evaluation or a live adapter test.

## Limits and next step

This does not complete SA1 or SA2. It does not persist across a service restart,
select evidence using a model, display a streamed incident timeline, or contain
live source-local adapters. The next candidate must define immutable producer
schemas and one credential-free adapter fixture, then connect it behind an
individually disableable read-only service boundary. No reasoning setting,
tool authority, live service, model or credential path changed here.
