# M3 routing smoke experiment — frozen before execution

Compare an explicit lexical rule baseline with one dependency-free TF-IDF
nearest-neighbour challenger. No LLM routing, embedding download or training
framework is required. Both predict proposed labels only; no executor or broker
is reachable. These labels are hypothetical semantic categories, not grants or
claims that timer/home/calendar/private capabilities are deployed.

Freeze `routing-families-v1.json` before running either evaluator. It contains
30 independently authored semantic families across timer, home, media, fact,
calendar, public web, private/public join, sysadmin, ambiguity and private context.
Each has ten presentation-prefix variants, yielding 300 examples: 100 train,
100 calibration and 100 test. Entire families stay in one split. The wrappers
are strongly correlated formatting variants, not 300 independent user intents.
There are only ten independent test families. Labels are author-provided synthetic
expectations, not human gold or model-derived ground truth.

Train TF-IDF only on train families. Choose an abstention score threshold from
0, .1, .2, .3, .4, .5 using calibration family exact-match accuracy; break ties
in favour of the higher threshold. Fit IDF on train only. No test-data tuning.
Scores are similarity values, not calibrated confidence. Rules are fixed before
execution and may return clarification or abstention.

Report per-family status/label correctness, complete required-set exact match,
clarification success, abstention and prohibited-label violations. Retain both
weighted example and family counts, but interpret family counts. Positive
performance on this tiny authored corpus is insufficient for production adoption.
No automatic winner: retain rules unless a representative independent corpus and
local-model evidence establish a meaningful benefit. A failure/inconclusive
result is retained and must not trigger same-test tuning. The next dataset version
must have new families and label review, not edited expected answers.
