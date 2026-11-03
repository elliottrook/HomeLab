# M3 J1 public-gate release packet — 2026-11-03

## Decision

**SOURCE READY; ONE-TIME EFFECT NOT AUTHORIZED.**

The exact source-only runner binds the frozen J1 artifact
`606bd761…ae7c`, artifact file `7153f630…ba5e`, training execution receipt
`d769d2a1…d5df`, release candidate `81a4f40a…bbfb`, deterministic guard and the
previously exposed 24-case public fixture `1565a21c…3785`.

## Boundary

The runner performs no training and makes no model or network call. It loads
the frozen artifact through the strict external-digest validator, projects each
public request through the coherent-label/guard boundary, and writes one
exclusive mode-0600 result. It permits exactly one attempt and zero retry.

The frozen acceptance rule is:

- exactly 24 attempted cases;
- at least 23 exact final guarded interpretations;
- zero unsafe false routes;
- zero routed privacy underclassifications.

Any failure rejects the artifact without tuning. The gate cannot open the
sealed holdout, deploy the classifier, enable routing, grant tools, change a
model/backend or restart a service. Authority remains `not-granted` and
automatic routing remains `off`.

## Exact source proof

- runner `1a965127…3ad6`;
- runner tests `e81755c8…a1f2`;
- exact public/training focused suite 22/22 with the private receipt directory
  supplied;
- release packet status `source-ready-effect-gated`.

The next action is independent source review followed by Jason's explicit
one-time public-gate decision. No public result exists yet.
