# M1/D4 single-run Doctor producer — source candidate

**Date:** 2026-10-25  
**Status:** source-only candidate; no deployment, schedule change, capability grant or model egress  
**Predecessor:** `697b25da` fixed Doctor capability candidate

## Decision

The normal scheduled report previously ran `doctor.sh`, saved its human output,
then invoked `build-aster-health-report.py` in captured-input mode. The
producer-owned `aster.agent_inference` event is available only through a
private inherited file descriptor during a fresh Doctor invocation. A second
run would not be the same observation and could overlap or disagree with the
normal report.

This candidate makes the report builder own exactly one Doctor run. That run
now produces four separate artifacts:

1. the existing schema-1 aggregate report;
2. a schema-2 sidecar containing only fixed check ID
   `aster.agent_inference`, its typed state, run ID, timestamp and the exact
   schema-1 byte digest;
3. the full operator transcript retained locally at mode `0600`; and
4. a content-free scheduler result containing only Doctor's exit code.

The normal human log and generic alert logic continue to use the private
transcript. No transcript or free-text summary is added to the sidecar.

## Publication boundary

When explicitly deployed later, the existing publisher would send one
base64-encoded JSON envelope over the existing fixed SSH/`pct exec 104` path.
The guest-side fixed writer validates both schemas and their digest binding,
then writes exact bytes to:

- `/var/lib/aster/health/latest.json`; and
- `/var/lib/aster/health/aster-inference.json`.

Both targets remain root-owned, group `aster`, mode `0640`. The aggregate is
replaced first and the sidecar second. A reader racing either replacement sees
a digest mismatch and must return `unavailable`; it cannot trust a mixed pair.
All local artifacts use unique temporary files, mode `0600`, and atomic
replacement, including when a destination was previously a symlink.

## Validation

The focused producer/scheduler suite passes **7/7**. It proves:

- one Doctor invocation feeds the aggregate, structured sidecar, private
  transcript and existing scheduled report;
- the published envelope preserves the exact bytes used for the digest;
- private Doctor text appears only in the local transcript and schema-1
  operator report, never the schema-2 sidecar;
- missing, duplicate, wrong-run and malformed producer events abstain;
- captured-input compatibility remains available for other callers;
- output destinations must be distinct; and
- symlink destinations are atomically replaced without writing their targets.

The downstream adapter, model projection and fixed-capability suites pass
**16/16**. Combined candidate coverage is therefore **23/23**.

Source SHA-256 values:

| File | SHA-256 |
|---|---|
| `scripts/build-aster-health-report.py` | `8ec44150b11e362896ad9662fed9cb0b26798c28a56ec6d447208d5cf67e23d7` |
| `scripts/scheduled-report.sh` | `76611cdef24340ec13dd8275c7237cb8d8f8b61d38a97a6ed09afebb500b544e` |
| `scripts/test_build_aster_health_structured.py` | `90d93b94cc3df6ca6ed74015476460be4f9adc64211b4a59bb1ff09244f07ba0` |
| `scripts/test_scheduled_report_structured.py` | `65838ba99716e0dd91db38fda04008bb3efd701dc78bcc41e0b668f449bcdc5e` |

## Remaining gates

This result does not install the producer or change the 08:15 scheduled job.
Before a live change, recheck the installed schedule and source hashes, freeze
the exact rollback copy, test guest ownership/group access, and separately
review the dedicated caller, broker registration and gateway projection. A
live producer deployment and any capability grant remain distinct changes.

