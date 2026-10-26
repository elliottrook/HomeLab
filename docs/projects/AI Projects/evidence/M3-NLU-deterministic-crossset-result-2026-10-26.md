# M3 NLU deterministic cross-set result — 2026-10-26

## Result

Neither deterministic challenger is eligible under the accepted NLU policy.
This is a development rejection, not a deployment or holdout result. Automatic
routing remains off and the independent holdout remains sealed.

The evaluation used all six spent, independently labelled 60-case calibration
sets. It retained the accepted all-case coverage denominator and recorded only
aggregate metrics. No request text, label or answer is stored in Git.

## Deterministic multi-head classifier plus policy guard

For each fold, the hashed multi-head classifier trained on five sets and was
tested on the sixth. The deterministic policy guard then applied privacy
floors, policy denials and capability normalization.

| Held-out set | Routed | Selective error | Eligible |
|---|---:|---:|---|
| 1 | 34/60 | 41.2% | no |
| 2 | 34/60 | 23.5% | no |
| 3 | 36/60 | 30.6% | no |
| 4 | 35/60 | 28.6% | no |
| 5 | 34/60 | 20.6% | no |
| 6 | 29/60 | 24.1% | no |

No fold satisfies both 60% coverage and the 10% selective-error ceiling.

## Frozen model outputs plus deterministic policy guard

The same guard was applied to the already spent local-model calibration
outputs. No new model call was made.

| Set | Valid | Routed | Selective error | Eligible |
|---|---:|---:|---:|---|
| 1 | 42/60 | 0/60 | 0.0% | no |
| 2 | 57/60 | 30/60 | 16.7% | no |
| 3 | 57/60 | 35/60 | 22.9% | no |
| 4 | 54/60 | 36/60 | 22.2% | no |
| 5 | 56/60 | 34/60 | 20.6% | no |
| 6 | 56/60 | 23/60 | 17.4% | no |

The guard removes some unsafe behavior but cannot turn either the model or the
hashed classifier into a qualifying router. Agreement filtering was also
measured during development; it removed unsafe false routes in the viable
folds but remained below coverage and above the selective-error ceiling.

The content-free aggregate result is owner-only at mode `0600`, SHA-256
`42b5b89cde224eda1ae6d6054c638f30508e04ed8985beb3a605480e31eaf14f`.

## Architecture decision

Do not create another independent calibration for these challengers. The next
implementation should use explicit deterministic recognizers only for narrow
high-precision intents and send everything else to the existing ordinary Aster
answer path or an explicit clarification path. That design must demonstrate the
accepted coverage on exposed development data before another private corpus is
created. It grants no route or tool authority by itself.
