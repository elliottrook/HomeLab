# SA0 current production/source reconciliation — 2026-10-26

## Result

**SOURCE CANDIDATE PASS; LIVE SA0 PARITY REMAINS OPEN.** A read-only check of
LXC104 found that the six narrow Lab Operations, Doctor and Speech runtime
files checked are byte-identical to this Stream A branch and their expected
services are healthy. The core `aster_agent.py` is not byte-identical.

The running core is the previously observed production composition at SHA-256
`7edc7ff9776357d62f6eff45de2093aab5749bb38317251b404df88012c6b50c`.
It contains the production OpenBao and privacy-minimized knowledge-usage
integration, but lacks later branch fixes for bounded Doctor reads, runtime
identity, passkey continuation and current Companion behavior. Blindly
replacing it with the former branch source would have dropped knowledge-usage
accounting.

## Reconciled release candidate

The missing production feature was composed into the newer reviewed source:

- `aster_agent.py`: SHA-256
  `e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116`;
- `knowledge_usage.py`: SHA-256
  `900a7fccad9c6e665297e3655e01844ca976705f69b45fac689858a00ccbfb55`;
- `aster-agent.service`: SHA-256
  `530b3918e08e8a9e27ce2f651b18fd4967bdba8c453eecc40b37788b4c9b1a15`.

The module and unit already match production exactly. Therefore the eventual
runtime change is one file only: `aster_agent.py`. No model, credential,
database, broker policy, capability, firewall rule or schedule needs to change.

The knowledge counter retains only timestamp, fixed persona, result count,
coarse source buckets and directory-first state. It does not retain request
text, excerpts, user identity or answer content. The new gateway call passes
only the result list to that counter.

## Verification

The composed source was copied into a root-only disposable LXC104 directory and
run with the installed Aster virtual environment. `test_knowledge_usage.py`
plus the complete `test_aster_agent.py` suite passed **99/99**. The temporary
packet and extracted directory were removed afterward.

Before and after this test, Aster Agent, Lab Operations broker, fixed Doctor
gateway, fixed Speech gateway and fixed Speech caller were active with zero
restarts. No running file, service, model, lease, schedule or retained state was
changed.

## Exact remaining effect

A live parity closeout requires a separately authorized one-file deployment and
restart because the user requires approval for system restarts:

- installer: `services/aster-agent/deploy/install_sa0_current_composite.sh`,
  SHA-256 `7ad4832c9eea4f1c23fec4eeb4eca817b9af37747018bd3d4860a5c41b4591e1`;
- installer contract test: SHA-256
  `b0dbd464f32f247968464bfdb7f848547ea042861ad4c3d6a02cc86ac8343540`;
- source-only installer checks: shell syntax plus **4/4** contract tests pass.

1. require the current live source hash above, root ownership/mode, healthy
   service and unchanged model service;
2. preserve that exact live file in a fresh root-only checkpoint;
3. stage the candidate, verify its exact hash and import it with the installed
   environment;
4. atomically install only `/opt/aster-agent/aster_agent.py` and restart only
   `aster-agent.service`;
5. verify service health, zero restart loop, ordinary unauthenticated denial,
   the read-only health endpoints, and byte parity with Git;
6. on failure restore the exact checkpoint, restart only Aster Agent and repeat
   the health and hash checks.

That action does not authorize a model restart/change, OpenBao operation,
Companion replacement, approval effect, routing change or other deployment.
