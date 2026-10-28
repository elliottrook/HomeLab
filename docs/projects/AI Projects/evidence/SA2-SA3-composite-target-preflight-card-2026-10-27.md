# SA2/SA3 composite target preflight card — 2026-10-27

Status: **prepared; wait until the protected overnight transaction is terminal**

## Decision

Prove that the exact single-restart composite still matches LXC104 and passes
under its Python 3.13 runtime before proposing the live installation. This
preflight is read-only with respect to installed application files and services.
It may create and remove one private temporary test directory; it cannot restart
a service, call a model, write an incident or install a candidate.

## Fixed inputs

- source commit: `cb2fb608aaaeb17e6fc1cd06f2f82dd8e7269bf1`;
- release packet SHA-256: `b03586e9ee9bf59de0c94aa6e78afa832dc10a28169d718f4a85dc024d63bfcb`;
- original target-validation packet SHA-256:
  `3a7137e07239b6f81b8d997ac054a9627d0955d9117ec182893b29d6d30c0279`
  (**rejected on October 28 because it omitted the pinned synthetic fixture**);
- corrected target-validation packet SHA-256:
  `ff07c5086ee3e5c2dde04a152927fa8ef68417b0d9814faf1261b2ec56c5f322`;
- target: Proxmox LXC104 `/opt/aster-agent`;
- target interpreter: `/opt/aster-agent/venv/bin/python`;
- expected test count: **72**.

## Admission

Run only after the exact-date F2/F3/F6/full-Aster services and reconciliation
are terminal, no whole-host lease or recovery is active, LXC104 and Aster Agent
are healthy, and no backup, pull or maintenance operation overlaps. A failed or
uncertain condition is NO-GO without staging.

Read the four predecessor paths without following links and require root:root
mode `0644` with these hashes:

| Path | Expected SHA-256 |
|---|---|
| `/opt/aster-agent/aster_agent.py` | `43af11c953fb63fdbc37cd7465fe69fb7b6d0c3cd64cff206d484e0398284613` |
| `/opt/aster-agent/doctor_incident_adapter.py` | `c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db` |
| `/opt/aster-agent/sysadmin_incident_store.py` | `c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb` |
| `/opt/aster-agent/sysadmin_registered_producer.py` | `b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd` |

Require the three proposal paths and every `.new` path to remain absent. Any
drift means stop and reconcile source; do not reinterpret the old installer.

## Target-Python proof

1. Rebuild both deterministic archives from the exact commit into new local
   mode-`0600` paths and require both recorded hashes.
2. Copy only the validation archive to a new root-owned mode-`0600` Proxmox
   temporary path, push it into a new root-only LXC104 temporary directory and
   recheck its hash before extraction.
3. Extract the corrected 17-member archive without overwriting any existing
   path. Sixteen members remain flat; the sole nested member is the exact
   `evals/sysadmin-producer-fixture.json` required by the frozen tests.
4. Run the nine `test_sysadmin_*.py` modules with bytecode disabled and
   `PYTHONPATH` ordered as the temporary directory followed by
   `/opt/aster-agent`. Require exactly 72 passes under the target interpreter.
5. Import the composite candidate and require both exact authenticated routes:
   `/v1/sysadmin/incidents/{incident_id}/propose` and
   `/v1/sysadmin/incidents/{incident_id}/observe`.
6. Remove the guest and host temporary validation copies. Verify no bytecode,
   runner, incident, model request, service restart or installed-file change.

## Result rule

GO requires exact predecessors/absence, both archive digests, 72/72 tests,
both routes, complete temporary cleanup and unchanged production health/PIDs.
The result may then support one highlighted approval request for the exact
seven-file installation and one Aster Agent restart.

Any mismatch, test failure, cleanup uncertainty or production change is NO-GO.
Record the first failed gate and prepare a corrected source packet; do not run
the installer and do not infer a retry. This card grants no deployment,
restart, model call, automatic route, observation execution or repair authority.
