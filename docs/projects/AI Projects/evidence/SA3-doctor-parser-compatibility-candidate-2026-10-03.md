# SA3 Doctor parser compatibility candidate

Status: **deployed; live Doctor result confirmation blocked by prior unknown job**  
Date: 2026-10-03  
Change class: implementation repair candidate; no live promotion decision

## Hypothesis

The Lab Operations worker can consume the current fixed Doctor summary safely
if its aggregate-counter parser accepts the documented emoji-prefixed form as
well as the legacy plain form. This will prevent a completed future Doctor run
from being rejected solely because of the presentation prefix.

## Evidence and limit

The observed private operation log was incomplete and had no final counters.
That does not establish the cause of its `unknown/interrupted` outcome. Source
inspection independently confirms that `doctor.sh` emits:

```text
🟢 Passed:   N
🟡 Warnings: N
🔴 Failed:   N
```

while the deployed worker searched only for unprefixed lines. The candidate
normalizes ANSI colour only, accepts an optional leading status emoji, and still
requires all three complete aggregate counters. It does not infer counts from
individual findings.

## Offline validation

- Existing legacy plain-counter fixture remains accepted.
- New emoji-prefixed fixture is accepted with the expected counts.
- Incomplete output is rejected.
- The full local worker suite passed: 20 tests.

## Deployment record

The worker-only repair was installed on the existing private Mac worker path on
2026-10-03. The previously deployed worker was preserved as a private rollback
copy with its original restrictive mode. The replacement digest matched the
reviewed candidate, retained mode `0700`, and the LaunchAgent restarted into an
active process. After a bounded observation, its error log remained empty and
no pending job existed.

The existing `unknown/interrupted` Doctor job was deliberately retained. It
blocks a new run under the Lab Operations safety model, so this deployment has
not yet been proven by a fresh live Doctor result. No job state was cleared and
no Doctor retry occurred.

## Remaining gate

Investigate and reconcile the prior interrupted job under the Lab Operations
uncertain-outcome procedure before any new Doctor run. Then perform one bounded
read-only Doctor observation and verify aggregate counts, bounded redaction,
result delivery and no collateral effect. This candidate cannot resolve an
interrupted execution by itself.
