# SA3 fixed local proposal transport — 2026-10-26

## Result

The source-only local-model adapter for the sanitized SA3 proposal boundary is
complete. It is deliberately narrower than the historical SA3 development
runner: one fixed accepted model endpoint, one call, no retry, no tools, no
thinking transcript, no producer access and no repair path.

No model call or live service change was made while freezing this source.

## Fixed behavior

- Endpoint: `http://192.168.70.12:11435/v1/chat/completions`.
- Model: `qwen3.5-9b`.
- Temperature zero; thinking disabled; non-streaming response.
- Forty-five-second request timeout, 512 output-token cap and 16 KiB response
  cap.
- Existing authentication is accepted only as a function argument and appears
  only in the HTTP authorization header.
- The request offers no tool schema or tool choice.
- The response schema constrains citations to supplied opaque references and
  target/kind values to the remaining sanitized catalogue. The trusted SA3
  boundary still performs the authoritative pair, citation, state and effect
  validation afterward.
- Duplicate JSON keys, multiple choices, tool calls, oversize bodies, malformed
  envelopes, missing authentication and transport failure all stop without a
  retry.

## Validation

- New transport tests: **6/6 passed**.
- Full `test_sysadmin*.py` suite: **60/60 passed**.
- `git diff --check`: passed.

## Source pins

| File | SHA-256 |
|---|---|
| `services/aster-agent/sysadmin_proposal_transport.py` | `ff94ebb2b4bc7aeb9e6694c6f1927b6c2658bcba0a814576b0203228644fa672` |
| `services/aster-agent/test_sysadmin_proposal_transport.py` | `3ae52f250dcf5526ace92d9bf4be9f7de9527370867d8b1ca7620a9943be24aa` |

## Next gate

Run a small, no-effect connected check using synthetic incident state only,
after independently confirming an idle healthy model service and no active
whole-host lease. Retain only proposal/decision metadata and bounded evaluation
results, never the credential or reasoning. Do not run near the F2 backup and
integrity window.
