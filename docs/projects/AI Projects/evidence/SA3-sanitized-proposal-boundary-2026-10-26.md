# SA3 sanitized proposal boundary — 2026-10-26

## Result

The source-only SA3 proposal boundary is complete and passes its focused
regression suite. It connects the current incident state to an injected future
proposal transport without giving that transport an incident identity, private
operator wording, private hypotheses, raw evidence IDs, producer source names,
tool execution or repair authority.

This is a code and contract milestone. It did not call a model, alter a live
service, execute an observation, create an incident or authorize a repair.

## Boundary

`sysadmin_proposal_boundary.py` builds one deterministic request containing:

- opaque state and evidence references;
- already-validated observation target, kind, time, state, summary, bounded
  facts and truncation status;
- only the still-unfilled pairs from the incident's preregistered observation
  plan; and
- literal `authority=none` and `effect=none` constraints.

It deliberately omits the internal incident ID, incident title, hypothesis
history, raw evidence IDs and producer source names. The module has no network,
filesystem, subprocess, credential, producer or model implementation. A caller
must inject one transport.

The response contract accepts only one exact schema. It requires the current
opaque request reference, citations drawn from the exposed evidence, a bounded
hypothesis summary and either a remaining registered observation pair or a
terminal disposition. It rejects stale responses, missing or invented
citations, repeated citations, unplanned or already-filled checks, malformed
fields, extra authority fields and summaries that claim an action was already
performed. Trusted code supplies the private incident ID and current state
digest, then revalidates the result through the existing SA1 selector. The
result continues to state `authority=none`, `effect=none` and, for an
observation, `execution=not performed`.

## Validation

- `python3 -B -m unittest discover -v -s . -p 'test_sysadmin*.py'`: **54/54
  passed**.
- The eight new proposal-boundary tests cover private-field omission, injected
  transport, stale state, citation integrity, remaining-plan selection,
  terminal output, malformed/effect-claim rejection and the initial no-evidence
  case.
- `git diff --check`: passed.

## Source pins

| File | SHA-256 |
|---|---|
| `services/aster-agent/sysadmin_proposal_boundary.py` | `6ed9fb670db1e51c97c5d7bad5e3def918bc27bf6400b78da64be69ec796453a` |
| `services/aster-agent/test_sysadmin_proposal_boundary.py` | `01d073143bfb4f62613e5dfa2716144f848c05f1db868195f906db56d6ec6d48` |

## Next gate

The next SA3 step is a model-transport adapter with fixed prompt and response
limits, followed by a no-effect evaluation against representative incidents.
That adapter must preserve this boundary and cannot execute producers or
repairs. Any connected model run remains separately subject to current shared
service and lab-hour gates.
