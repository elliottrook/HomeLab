# M3 NLU non-vacuous threshold-policy boundary — 2026-10-24

## Problem

The registered threshold-policy schema already required bounded coverage and
selective-error values, but the inclusive `[0, 1]` range admitted two vacuous
settings:

- `minimum_coverage: 0` could accept a candidate that routed no calibration
  cases; and
- `max_selective_error_rate: 1` imposed no useful accuracy constraint.

Either value could produce a syntactically valid frozen policy while supplying
no evidence that the NLU adds useful routing behavior.

## Correction

Registered and frozen policies now require positive minimum coverage and a
selective-error limit strictly below one. The existing zero-tolerance rules for
privacy underclassification and unsafe false routing remain unchanged. The
change sets no numeric release values, reads no calibration or holdout cases,
and does not select a threshold.

## Validation

The focused NLU suite passes **47/47** under the bundled Python environment,
including explicit rejection of both vacuous extremes. An initial system-Python
run executed 38 tests but could not import the existing Pydantic-dependent
module; no dependency was installed or changed. The complete pass used the
repository's established bundled dependency environment.

This is an offline policy-schema correction only. It does not register a
policy, collect labels, inspect holdout data, enable shadow routing, authorize
egress or grant execution authority.
