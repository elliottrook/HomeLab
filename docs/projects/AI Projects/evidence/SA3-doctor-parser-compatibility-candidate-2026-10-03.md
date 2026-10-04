# SA3 Doctor parser compatibility candidate

Status: **offline candidate; not deployed**  
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

## Promotion gate

Before any deployment, inspect the worker interruption separately, verify the
pinned Mac deployment copy and its source provenance, run the bounded local
validation in the deployment environment, define rollback, and obtain the
applicable live-change approval. This candidate cannot resolve an interrupted
execution by itself.
