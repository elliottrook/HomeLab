# M3 NLU Candidate-v10 calibration-v6 result and architecture decision — 2026-10-26

## Decision

**REJECT Candidate-v10 and stop prompt-only iteration.** Its one bounded,
tool-free calibration-v6 attempt completed all 60 cases, but the registered
selector found no eligible threshold. No threshold artifact was written, the
independent holdout remains sealed and automatic routing remains off.

Prompt-only versions v6 through v10 each improved a measured class and then
regressed another independent class. That is evidence that the accepted local
9B model is not stable enough to own the safety, privacy and capability
decision boundary. Continuing to add prompt clauses and spend fresh
calibrations is not a credible route to production admission.

## Frozen inputs

- Candidate-v10 artifact SHA-256:
  `ad01b3883a65125b1e37335b66d62a65d65103b98c8577ecd2a337833a2bcb39`
- Source SHA-256:
  `a0a85ba1e46e88c0a7557dcd8744530d336bef74f5cd1854d25ba31877a5da4d`
- Blind labels SHA-256:
  `c34ed167367d9b36023e084f764ef792e808ba575277e3c419cee429b7a3b5a1`
- Custody manifest SHA-256:
  `792ced736411d4cb3799da504cfcbe5b2db57c2554d6e8447b7c05e9615fa404`
- Normalized text-set SHA-256:
  `76a9d7164f63878babf6ef7fe4d836eb7270cbca8bc6a776cc60e93e3f438b6e`
- Release artifact SHA-256:
  `7b071050d4ac1db04b3b2d8a6202ec4c54293c4b80c9f6a7c907b89e6acd2c8e`
- Release canonical self-hash:
  `7923044977bece755ac6a534ccaf740363b55bc89b02ec02bfdc9ce723bc3c2d`
- Registered policy SHA-256:
  `c21cb32b8e37b5a6010c75766abffa49843fb2f0f49d316a4722a20dc7420975`

The fictional 60-case source has ten cases per family and zero normalized
overlap with public development or calibrations v1 through v5. Custody, blind
label review and release derivation remained separate.

## Result

- Run SHA-256:
  `a2e9355323315fea32fb2ac20a330b6cead50a0b42891622d37b3ae87c751569`
- Attempt-journal SHA-256:
  `6f9245ae1b5316c7f5ae50c125c3c5929072975d926ad85be2eb8699fb67ac9d`
- Score SHA-256:
  `7c18437631aa0404bc47edb053fd9deddd81c05ac4ae9b75c31e460c14ea6527`
- Attempts: `60/60`
- Structurally valid: `56/60`
- Routed: `25/60`
- Safe and exactly correct routed rows: `22/60`
- Privacy underclassifications: `1`
- Unsafe false routes: `0`

Coverage was 41.7%, below the registered 60% minimum, and the privacy floor
also failed. The selector exited `2` and no selected-policy file exists.

## Post-run feasibility defect

The calibration design had only 30 target labels with disposition `route`.
The accepted policy requires at least 36 of 60 cases to route while permitting
zero routes whose target disposition is not `route`. Its theoretical maximum
safe coverage was therefore 50%, below the required 60%. The calibration was
incapable of selecting a threshold before Candidate-v10 was run.

This does not reverse the rejection: Candidate-v10 independently violated the
zero privacy-underclassification floor. It does mean the 41.7% coverage result
must not be presented as model-only evidence. A new fail-fast feasibility check
now computes the required routed count and maximum routed count allowed by the
unsafe-route constraint before a model run is admitted.

## Deterministic-guard feasibility check

A source-only deterministic guard prototype encodes the three v4 safety
classes, sensitivity floors and minimal canonical capabilities. Five focused
boundary tests pass. Replaying it offline over Candidate-v10's already-spent
v6 outputs produced 25 routed rows, 20 exact routed rows, 20% selective error,
one privacy underclassification and zero unsafe false routes. This is useful
directional evidence but it does not meet the accepted policy and cannot be
promoted or used to open the holdout.

A dependency-free hashed lexical classifier was also evaluated with each one
of the six 60-case calibrations held out in turn. It produced 40, 50, 45, 48,
49 and 45 exact interpretations respectively. This is materially better
semantic evidence than the prompt-only loop but still produced privacy
underclassifications and unsafe routes. It is a development challenger, not an
admitted policy owner or route.

## Architecture correction

The next NLU candidate must treat deterministic policy as the owner of
deny/abstain, sensitivity floors and capability allowlisting. A local model may
propose semantic interpretation only inside that envelope. The challenger must
be evaluated first on the six now-development calibration sets with a frozen
rule set or other reproducible local classifier, then receive a new independent
calibration only if it clears all registered constraints without tuning on that
new set.

This preserves the project's original principle that routing never grants
authority and aligns with the earlier routing smoke, where fixed rules
outperformed a small statistical challenger. It is an offline design decision,
not a deployment or automatic-routing release.
