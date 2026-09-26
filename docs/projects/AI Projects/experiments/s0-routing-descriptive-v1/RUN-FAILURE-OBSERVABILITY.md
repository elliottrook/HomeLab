# Bounded run-failure observability

Date: 2026-09-26
State: implemented and locally validated; no live invocation

## Problem

Run 002 safely failed during preflight, but its terminal record retained only the
broad lifecycle stage. The preceding resource record narrows the failure to the
interval between resource journalling and `preflight-verified`; it cannot prove
whether DNS transport, DNS response validation or journal persistence failed.
Inferring a cause from a later successful DNS query would contaminate the evidence.

## Contract

Future lifecycle failures add two bounded, non-secret fields:

- `failure_boundary`: a code controlled by the lifecycle, such as
  `command-health`, `health-validation`, `preflight-dns` or
  `preflight-journal`;
- `failure_class`: exactly one of `timeout`, `permission`, `io`, `validation`
  or `internal`.

No exception message, traceback, command output, hostname, path supplied by an
exception, credential material or model-generated explanation is retained. The
existing stage, mutation and manual-recovery fields remain authoritative.
Keyboard interrupts retain the existing durable interruption semantics and are
not converted into ordinary caught failures.

## Security and authority

These fields improve evidence only. They do not authorize a retry, cleanup,
permission change, alternate transport or broader diagnostics. The one-shot
run-002 approval remains consumed, and its journal is immutable. A future live
attempt requires a distinct journal, reviewed manifest and explicit authorization.

## Validation

Local tests inject a DNS timeout containing a sentinel secret and an I/O failure
while writing `preflight-verified`. The records contain only the allowlisted codes,
distinguish the two boundaries and omit the sentinel. Default denied transport is
classified as `permission` at `command-load-state`. The complete adaptive suite
passes 210 tests. No SSH, DNS, LXC, package, corpus or remote-Git operation is part
of this observability milestone.

## Decision

Retain this schema for any future candidate. Do not reinterpret run-002 using the
new fields; they did not exist in the executed manifest. The next safe task is a
local design review of whether a third live fixture attempt has enough expected
information gain to justify shared-host risk. A third attempt is not assumed.
