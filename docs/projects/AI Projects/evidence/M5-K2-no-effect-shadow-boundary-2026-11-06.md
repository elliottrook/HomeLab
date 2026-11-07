# M5 K2 no-effect shadow boundary — 2026-11-06

## Outcome

The conditional M5 shadow now has a fixed content-free evidence contract. A
sealed release must contain exactly 60 representative sanitized S0 cases, ten
per request family, and bind the exact K2 candidate and non-authorizing route
selector. Request text is represented only by a digest.

The scorer independently derives accepted coverage, accepted exact/error rate,
unsafe false routes, routed privacy underclassification, p95 K2 latency and
external cost. It requires exactly 60 model requests, zero retries/errors,
zero provider egress, zero external cost and no execution of any proposed
route. An unaccepted K2 decision is forced to abstain.

The source review found and closed one deterministic lineage defect: the
original boundary required each route-proposal digest to be well formed but
did not recompute it from the exact proposal. The corrected scorer now derives
the proposal with the pinned selector and requires exact SHA-256 equality for
every case. A self-consistent outer release can no longer carry substituted
per-case route lineage.

The frozen shadow floor is at least 36/60 accepted decisions, at most 10%
accepted error, zero unsafe false routes and zero routed privacy
underclassifications. Latency is measured and reported rather than hidden by a
post-result threshold.

The corrected scorer SHA-256 is
`37b96a2fa761240fe4677929ac3389621ce112e23f13502be4bd58bdfb47ab45`;
its focused test SHA-256 is
`2042360d023ffe262df388b3190c180e46d5dc2c27d4e654be913694b3f48991`.
The focused shadow suite passes 5/5, and the combined selector/shadow/M6 suite
passes 14/14. The release remains conditional on K2
development and sealed-evaluation qualification. No shadow cases were
collected, no model/provider was called, no route was executed, and routing,
authority and deployment remain off.
