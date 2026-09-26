# Assessment evidence

- `source-manifest.json`: original source hashes at e50b670b906f397e1e70b6d51cf07e88235ac5c5. The `source-snapshot` paths describe the original review bundle, not files deployed here. Source links in the assessment resolve to that immutable Git revision.
- `broker-probe-results.json`: historical synthetic observations at the baseline revision; no production actions.
- `probe_broker_boundaries.py`: original historical probe, preserved unchanged. To reproduce it verbatim, supply the baseline `source-snapshot/ops/credential-broker` tree alongside it. For current executable regressions, use `ops/credential-broker/test_adaptive_foundation_regressions.py` from the repository root.
- `live-broker_service.py`: non-secret source evidence from the original read-only inspection, not executable deployment configuration. The extra terminal blank line from the review copy was removed during adoption; the archived source now matches the recorded live SHA-256.
- [M0 baseline](M0-baseline.md): project-start evidence and exact next gate.

No runtime data, credentials or personal interaction datasets are included. Original raw web-research captures remain in the local assessment bundle; the checked-in documents cite authoritative primary sources directly.

- [Stage1 deployment](M1-stage1-deployment.md): approved two-file production change,
  checkpoint, readiness incident/recovery and bounded observation evidence.
  The original assessment probes above remain historical.
