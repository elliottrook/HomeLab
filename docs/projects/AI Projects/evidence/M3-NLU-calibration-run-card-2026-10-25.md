# M3 NLU 60-case calibration run card — 2026-10-25

> State: **READY FOR STATIC PREFLIGHT; LIVE RUN REQUIRES ONE EXACT APPROVAL**
>
> Effect: sixty synthetic, local, tool-free classification requests; no route
> or production change

## Decision value

Run the sealed candidate once over the independently created and reviewed
calibration release, derive its content-free score and either freeze the first
threshold satisfying the accepted policy or record a calibration rejection.
Shared/offline work can validate the mechanism, but only local inference can
measure the candidate.

## Exact inputs

- private source SHA-256:
  `6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e`;
- normalized source-text-set SHA-256:
  `c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3`;
- calibration artifact SHA-256:
  `f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1`;
- registered-policy artifact SHA-256:
  `85b5090f929c50cba02d914418c1187bb9a7d848f05c38b174f125f77442df0a`;
- candidate artifact SHA-256:
  `456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897`;
- model SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- model-policy SHA-256:
  `57887883010ac682d50af9931b0dc80c71d2fe3b41309bf7b772fec70f4ed179`;
- endpoint: accepted local `aster-llama` chat-completions endpoint only; and
- runner source commit: `b5b235742ad120f9e40c795ab4352061da2218bb`, with runner SHA-256
  `484a09d4d1655336808767ead76d7803f6eadf783bbda5bdf1eaec8726389833`;
- scorer SHA-256:
  `ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd`;
  and
- threshold selector SHA-256:
  `9edc0317fe655bfc49b888d755155393cdc468e11bccc27dbe4881b886922cbb`.

## Bounds and custody

- exactly 60 synthetic cases, ten per request family;
- one attempt per case, concurrency `1`, temperature `0`, at most `256` output
  tokens, `90` seconds per request and `1,200` seconds total;
- no tools, web, cloud egress, route execution or connected capability;
- the existing local service key is read only inside LXC110 and never printed,
  copied into arguments or written to evidence;
- raw request text remains in the owner-only source; raw model envelopes are
  parsed in memory and discarded;
- the attempt journal, run, score and threshold artifacts are new owner-only
  mode-`0600` files;
  Git receives only content-free receipts and fixtures; and
- an invalid response is retained in the denominator without retry. A transport
  uncertainty, timeout, endpoint failure, lease loss, pin drift or service
  health failure stops the remaining run and forbids replay under this card;
- each HTTP timeout is reduced to the remaining total wall budget, so a late
  case cannot extend the 1,200-second run deadline; and
- a partial run is retained for reconciliation but the runner exits nonzero.
  It cannot be mistaken for a completed calibration command; and
- the runner reserves both evidence paths before inference and durably records
  `attempt_started` before each request plus a content-free completion/error
  row afterward. A started row without a recorded row is an uncertain attempt
  and forbids replay.

## Fresh preflight

Immediately before the first request, require all of the following:

1. a compatible live whole-host `ai-lab` lease owned by this exact run;
2. no F2 scan, backup, TrueNAS pull, News run, other benchmark or maintenance;
3. accepted `aster-llama.service` active, authenticated and idle;
4. installed model, unit/runtime, runner, source, release and policy hashes
   equal the pins above;
5. LXC104/110/116 and required production services healthy; and
6. enough lease and wall-clock budget for 20 minutes plus restoration reserve.

A failed or uncertain gate means no model call. The lease must be released and
normal production health rechecked after every terminal outcome.

## Result path

If all 60 records exist, independently verify the exact attempt journal against
every final record, bind its digest into the content-free calibration score and
run the exact registered threshold selector. A valid frozen threshold
is calibration evidence only. A rejected threshold is a measured candidate
rejection. Neither result opens the independent holdout, deploys the NLU,
enables shadowing or automatic routing, or changes the accepted B60 runtime.
The scorer and selector each create a new owner-only mode-`0600` artifact and
refuse to replace existing evidence; their command summaries contain only
schema, count/status and digest fields.
