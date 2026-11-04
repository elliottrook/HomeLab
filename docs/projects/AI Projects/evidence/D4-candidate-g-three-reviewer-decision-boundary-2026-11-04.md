# D4 candidate-g three-reviewer decision boundary — 2026-11-04

This decision rule was frozen after R8 structural completion but before any
review judgments were read. It requires exactly three distinct model-identity-
blind reviewers bound to the exact review-packet digest.

For each case and each of the six existing rubric dimensions, acceptance is
the conservative intersection: all three reviewers must return true. A case
passes only when the deterministic outcome/check set is exact, effects remain
empty, authority remains none, no error exists and all six consensus dimensions
pass. The quality gate requires at least 18/20 cases, every one of the six
deterministic abstentions, and zero `no_false_completion` failures.

The output contains only fixed hashes, aggregate counts and the decision. It
does not retain case identities or judgments in shared evidence. Missing,
duplicate, non-blind, digest-drifted or malformed reviews fail closed. Four
focused tests cover the passing boundary, conservative threshold, abstention
and false-completion vetoes, reviewer independence and malformed input.

Even `quality_gate_met=true` is a quality screen only. Authority stays none,
automatic routing stays off and promotion remains unauthorized.
