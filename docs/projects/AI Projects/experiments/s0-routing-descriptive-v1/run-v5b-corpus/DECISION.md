# S0 descriptive experiment decision

Decision: **ACCEPT RESULT / RETAIN BASELINES / DO NOT PROMOTE**

The corrected run answered the preregistered finite-corpus questions. Keyword rules
beat always-abstain; fixed-threshold nearest beat keyword rules; and supplied
synthetic context changed predictions, improving nearest on two cases while making
keyword rules worse on one. These are useful error-shape and disagreement findings.

No candidate is ready for production routing. Ten exposed development families
cannot establish generalization, confidence calibration, privacy behavior or
regression resistance. Nearest's higher completeness also came with extra and
missing capability errors. Context was not uniformly beneficial. Selecting the
largest complete count would discard those safety and data-quality distinctions.

Retain always-abstain as a safety/control baseline, keyword rules as the cheapest
deterministic baseline, and fixed nearest as the first routing challenger. Use
their recorded disagreements as candidates for future independent labeling. Do
not tune the 0.2 threshold against this exposed set.

The disposable VM remains the accepted offline experiment boundary. Its roughly
135-second lifecycle for 0.118 seconds of evaluator work rules it out as a serving
harness. M3 must compare serving harnesses separately and account for startup,
dependency, prompt/token, call, retry, maintenance and steady-state overhead.

This closes only the S0 descriptive comparison. M3, M4 and all production or
shadow gates remain open. VM123 and its evidence remain retained; cleanup and Git
push require separate authority.
