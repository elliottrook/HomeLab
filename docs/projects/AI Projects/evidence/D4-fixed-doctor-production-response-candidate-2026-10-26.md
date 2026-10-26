# D4 fixed Doctor production response candidate — 2026-10-26

## Candidate

The qualified deterministic response is now integrated into the source form of
the dedicated fixed Doctor caller. The broker and gateway still return the
same bounded structured observation. The caller validates that observation,
renders the qualified text, and returns a version-2 presentation containing:

- the unchanged structured observation;
- deterministic user-facing text;
- the exact fixed capability identity; and
- literal `authority: not-granted`.

No model call, tool grant, broader Doctor read or automatic route is added.
Malformed, stale, oversized-age, wrong-source and wrong-fact observations fail
closed before presentation.

## Source identity

| File | SHA-256 |
|---|---|
| `fixed_doctor_caller.py` | `d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48` |
| `fixed_doctor_response.py` | `c7855a76da7f9a060dac4d4230c06703cd8be043b78a38445c47854b3fac70ff` |
| `fixed_doctor_capability.py` | `7c0fd1bcc3404661052627ec7d2fa04e811149f43fb3ea23bc27edf57bb5fb3b` |
| `doctor_structured_incident_adapter.py` | `aa282d2d5abc762228fec1d4ace01c4302c6712abd60e307a846e2c5a5058b02` |
| `doctor_model_projection.py` | `8fda9190f46ba836d9cf613729650894adf35e99ef7aadb1ae921c540f00c641` |

The focused caller/response suite passes 7/7. The wider fixed Doctor
qualification and service suites remain passing. This source candidate is not
installed or running.

## Deployment boundary

The next safe action is an additive, inactive candidate-directory installation
and isolated target-Linux import/test. That does not replace the live caller or
restart a service. Replacing the live caller requires a later explicit restart
approval, a checkpoint of the installed bytes, a bounded canary and rollback to
the currently running schema-1 caller.
