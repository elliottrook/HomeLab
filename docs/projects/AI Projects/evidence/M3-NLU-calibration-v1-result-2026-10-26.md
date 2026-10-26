# M3 NLU calibration v1 result — 2026-10-26

> Decision: **CANDIDATE V1 REJECTED; NO ROUTING AUTHORITY**

Jason explicitly authorized Stream A to use the shared AI stack for bounded
evaluation without waiting for exclusive lab hours, including harmless overlap
with an occasional News check. A system restart remained separately gated.

The exact root-custodied 60-case packet, accepted Qwen3.5-9B Q4_K_M model,
llama.cpp/SYCL runtime and service health passed fresh checks. No backup,
maintenance job, existing runner or prior output was present. The tool-free
runner completed once with all 60 attempts. The protected run and journal were
copied to owner-only Mac custody and independently reconciled before scoring.

Content-free result:

- attempted: 60;
- structurally valid interpretations: 42;
- invalid responses retained in the denominator: 18;
- dispositions among valid outputs: 37 clarify, 4 deny, 1 abstain, 0 route;
- run SHA-256: `7fd0571b48cf2655861366eadf74cfc7794dce3e8612196d0f1d0475b21a243a`;
- journal SHA-256: `ae8ee5995f9a4bb540b52e7b962482f10534526df27f8c2d0f90109c9aa19c4c`;
- score SHA-256: `0ee0c1df437cfef0b5b7098a772df805ee13abe632b72eb10a9aa5465faac145`.

The frozen selector found no threshold satisfying the accepted minimum 60%
coverage, maximum 10% selective error, zero privacy underclassification and
zero unsafe false-route constraints. It therefore created no threshold
artifact. The independent holdout remains unopened and the conditional holdout
card expires unused for Candidate v1.

The public candidate prompt contained the contradictory phrase “Never claim a
route” while asking the model to choose a disposition that included `route`.
Candidate v2 will correct that instruction and will be developed only against
the exposed 24-case fixture. Candidate v1 calibration text and labels will not
be used for tuning. A later candidate requires a newly bound calibration
release before any threshold can be frozen.

Postchecks found the model, Aster Agent, Speech and News healthy with zero model
service restarts. No route, tool, holdout, cloud egress or production setting
changed.
