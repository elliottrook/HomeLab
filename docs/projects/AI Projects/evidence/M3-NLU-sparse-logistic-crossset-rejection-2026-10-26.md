# M3 NLU sparse logistic cross-set rejection — 2026-10-26

**Decision:** **NO-GO — reject before independent calibration**

This offline development trial tested a materially different supervised
representation after the prompt ensemble failed. Four multinomial logistic
heads used fixed 4,096-bucket word unigram/bigram and character 3–5 gram
features to predict family, sensitivity, capability set and decision tuple.
Each outer fold trained on five of the six already-exposed 60-case development
sets. Thresholds were selected only from inner leave-one-set-out predictions
among those five sets, then applied to the untouched outer set.

The fixed exploratory source had SHA-256
`bebe2454cbcf65b09e8ab1826eb19dbaddb547cdea5441bcda9544238b3720dd`.
It used Python 3.12.14 and NumPy from the bundled offline workspace runtime.
No model endpoint, network, production service or sealed holdout was used.
Private request text and labels remained in their existing owner-only local
directories and were not printed or retained in Git.

All six outer folds stopped at threshold selection with
`no_inner_threshold`. Across each 300-row inner prediction set, raw exact
interpretations were only 61–75. The largest zero-unsafe, zero-privacy subset
covered only 6.3–15.7%, depending on the fold; the accepted policy requires
at least 60% decision coverage and at most 10% accepted-decision error.
This is a representation failure rather than a marginal threshold miss.

The candidate is rejected. Do not create a fresh calibration, open the sealed
holdout, enable routing or tune another sparse lexical variant against the same
six exposed sets. The remaining M3 path needs a demonstrably stronger semantic
representation or independent confidence source.

