# M3 post-J2 successor probe rejection — 2026-11-06

## Decision

The first three post-J2 development probes are **rejected**. They were
disposable, Mac-local aggregate experiments over only the admitted 768-row
training and 192-row validation split. The sealed 32-case evaluation was not
opened, B60 was not used and no production state changed.

These probes are diagnostic evidence, not release candidates. They do not
authorize another training effect, evaluation access, routing, deployment or
promotion.

## Measured aggregate results

| Probe | Best validation result | Frozen-policy result | Decision |
|---|---:|---|---|
| Joint character/word multinomial Naive Bayes | 109/192 exact | maximum zero-error accepted coverage 21/192 | Reject |
| Hierarchical field-wise whole-label Naive Bayes | 116/192 exact | maximum zero-error accepted coverage 21/192 | Reject |
| Apple NaturalLanguage word-embedding centroid/kNN family | best raw configuration 150/192 exact | best zero-safety-failure coverage remained 21/192; the equal-weight field-wise candidate was 146/192 exact and had 20 errors in its top 116 decisions | Reject |

The accepted confidence-policy v2 requires at least 60% decision coverage,
at most 10% accepted decision error, zero unsafe false routes and zero routed
privacy underclassification. No threshold pair for the strongest embedding
probe met all four constraints. Its top-116 decision error was 17.24%, and
the all-row result included sixteen unsafe false routes. Privacy
underclassification remained zero.

## Custody and safety

- raw admitted corpus content was not added to Git or shared evidence;
- only content-free aggregate metrics and disposable prediction IDs/scores
  were inspected;
- disposable prediction SHA-256:
  `0a56a85085dee719cf9b6a1f0d5f2d83dc6dfeb6ad5b16f4373687939e555b34`;
- disposable Apple NaturalLanguage probe SHA-256:
  `11f61a2a64025de017a89c1ff4abce65d2f92714f58210b4319e48107a1773a6`;
- sealed evaluation accessed: false;
- production changed: false;
- services stopped: zero;
- B60 used: false;
- automatic routing and tool authority: off.

## Consequence and next action

The probes confirm that simple lexical restatements, whole-label classifiers
and fixed OS-local embedding neighbours do not close M3. Further tuning of
these families against the same validation rows is closed. A successor must
change the representation or task formulation, be preregistered before a new
effect, and preserve a fresh untouched evaluation boundary.

While that materially distinct design is prepared, Stream A continues the
independent SA4 source/inactive-install lane. M3 remains open and automatic
routing remains off.
