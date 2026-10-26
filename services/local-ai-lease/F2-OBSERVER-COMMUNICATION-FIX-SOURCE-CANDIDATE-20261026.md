# F2 observer communication fix — source candidate

Status: **SOURCE-ONLY; INACTIVE INSTALL NOT AUTHORIZED**

The October 26 final gate failed because the real default launcher was
`subprocess.run`, while the coordinator treated its return value as a live
Popen object and called `communicate()`. The observer child did launch, but its
output was discarded; no accepted result was retained. The spent cycle must
not be retried.

## Fixed source

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193` |
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `2a21d2427a7110227cd7bbef0d6dcc5aae6ff97432dc0c102ffb49df8fc2032a` |

The coordinator now defaults to `subprocess.Popen` and retains the existing
bounded `communicate()` timeout, process-group kill, stderr suppression and
external deadline behavior. An explicit regression patches the real default
launcher binding and verifies `start_new_session=True`; injected Popen-like
tests remain for bounded failure cases.

## Validation

- Focused coordinator suite: **15/15**.
- Broader `test_f2*.py` suite: the source behavior passes; the active deferred
  card was updated to the new source/test pins.
- No F2 installation, schedule change, retry, scanner, receipt, lease,
  consumer stop, or model call occurred.

The next inactive-install card must recheck the installed prestate, install
only this coordinator/tested source, exercise the real installed entrypoint,
and preserve the spent October 26 state as terminal evidence.
