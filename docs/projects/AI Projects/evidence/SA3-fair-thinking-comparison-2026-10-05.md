# Fair local diagnosis comparison: thinking off versus on

Status: offline evaluator candidate built; connected comparison not run.
Owner: Jason. Coordination: this single Codex conversation.

## Practical question

Can the existing local model diagnose unfamiliar lab problems usefully when it
has adequate evidence and time to think? Compare correctness and practical waiting
time before considering a new model, cloud spending or hardware. Thinking disabled
does not mean a model has no reasoning ability; it removes an explicit inference
mode. Neither mode is presumed superior.

## Verified on 2026-10-05

A read-only allowlisted process query on LXC 110 found the running llama-server
with `--reasoning off --reasoning-budget 0`. Its executable's `--help` documents
on/off/auto reasoning and a thinking-token budget: zero ends immediately, positive
values are bounded. No service flags were changed and no model request was sent.
The help also distinguishes reasoning format from reasoning enablement: hiding
or extracting thought text is not the same as switching thinking off.

Primary reference: [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
Live binary behavior takes precedence over newer documentation. Request-level
override compatibility with this model/template is UNKNOWN until an approved
development smoke test proves it. Do not label a request thinking-enabled merely
because its payload says so.

## Paired experiment design (proposal; freeze before held-out runs)

| Condition | Non-thinking baseline | Thinking challenger |
|---|---|---|
| Model/quantization, host and context | Same pinned artifact and build | Same |
| Evidence, visible capability catalogue, prompt and grading | Same | Same |
| Answer capacity | Starting development target: 1,024 tokens | Same answer headroom |
| Additional thinking allowance | 0 | Starting development target: 1,536 tokens |
| Investigation deadline | Same, maximum five minutes | Same |
| Authority | Simulated read-only evidence only | Same |

These budgets are development starting points, not a claimed working API mapping.
If max_tokens includes both thinking and answer tokens, allow the challenger's
combined budget (initially 2,560), while preserving the same answer requirements.
Confirm exact accounting, context headroom and template behavior on development
fixtures. Freeze final settings before opening new holdouts; do not starve the
thinking arm with the old 96/128-token answer limit. The additional compute is the
intervention, so report its measured cost rather than pretend compute is identical.

Use paired fresh cases, serial requests and balanced alternating order. Record
warm/cold state, cache handling and shared-service load; never run both arms in
parallel on the single serving slot. No silent retry: capture timeout, truncation,
format error and unavailable service distinctly. Hash the model shards, server,
template, runner, cases and scorer. Retain finish reason, latency, token counters
where actually supported and reasoning-mode verification metadata. Discard private
reasoning text; save only the bounded answer and operational measurements.

First use public synthetic development fixtures to prove that mode control works,
the output fits and scoring behaves correctly. No private holdout is used for
budget tuning. Use the existing 20-case/18-pass quality screen and at least four
insufficient-evidence cases only after the protocol and fresh corpus are frozen.
Score every case in both arms without adapting the prompt or grader after results.
Twenty cases support a bounded pilot decision, not a universal reliability claim.

## What the test measures

Stage 1 is a diagnostic screen: select useful next checks from a visible catalogue,
explain the evidence briefly and ask for clarification when needed. The new offline
`sa3_fair_scorer.py` enforces exact identity coverage, visible vocabulary, empty
effect claims, complete output and separate model-blind review of meaning. Ordinary
summary wording is not compared with an exact answer string. Review records are
attestations, not proof of independent custody; name the reviewer and retain the
single-operator limitation if independent review is unavailable.

Stage 2, only for a promising candidate, must simulate a bounded multi-step incident:
the model requests registered read-only checks, receives fixed evidence, revises its
diagnosis and proposes verification. Both modes get identical tools, permissions,
maximum check count and evidence access. No shell or live production control.
Stage 1 alone cannot qualify a general sysadmin or an autonomous repair operator.

Assess correct diagnosis/checks, evidence use, stale-data handling, scoped proposals,
verification, abstention and false success claims separately. A model does not earn
safety credit just by repeating safety labels. Report time to first useful evidence,
total time, completion failures and useful coverage alongside quality. Existing
targets remain first evidence within 30 seconds, routine triage p95 within two
minutes, and a bounded five-minute complex investigation; report small-sample limits.

## Decision and boundaries

- Better thinking-enabled quality at usable latency: candidate for a finite local
  read-only pilot, with thinking reserved for diagnosis if simpler tasks need speed.
- Better quality but unacceptable latency: serving/performance investigation, not
  automatic new hardware purchase.
- Both modes inadequate after this finite trial: narrow Qwen's role and consider a
  separately authorized stronger-model comparison. Do not endlessly tune the test.
- Similar outcomes: prefer the simpler/faster option within the measured scope.

The offline evaluator and fixture tests are implemented; no inference runner or
simulated investigation engine is claimed complete. Next is development-only
request construction and mode-verification design. Before a connected run, bind
the exact settings/target, service-load limits and recovery path under the existing
project gates. The shared server must not be restarted or changed simply to run
this comparison without that bounded deployment decision. No cloud, new hardware,
credentials, production permissions or remote Git write is included.
