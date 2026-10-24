# M3 NLU contract boundary — 2026-10-24

Jason approved formalizing Aster's previously implicit NLU function while Stream
A continues independently of lab-hours work.

`RequestInterpretation` now separates request understanding from route selection
and authority. It records bounded family, sensitivity, capability needs,
ambiguity, disposition, reason and engine/policy provenance. Raw request content,
entity values, confidence claims and authority are rejected. The only accepted
authority value is `not-granted`.

Focused validation passed 6/6:

```text
RequestInterpretationTests       4
DecisionSemanticTests            1
OutcomeSemanticTests             1
```

The full historical adapter suite was also invoked. Its 19 adapter-dependent
tests stopped at the known fail-closed reviewed-source mismatch; the six isolated
semantic tests passed. The source definition was not repinned because this NLU
contract does not revise or rerun that historical experiment.

No service, model, provider, network client, egress rule, capability projection,
AI-PAM grant or automatic route changed. The design and later promotion gates are
recorded in [Aster NLU and selector boundary](../NLU-Selector-Boundary.md).
