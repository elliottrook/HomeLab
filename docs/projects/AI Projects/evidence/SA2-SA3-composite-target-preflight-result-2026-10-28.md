# SA2/SA3 composite target preflight result — 2026-10-28

Decision: **GO for the separately gated installation and one Aster Agent
restart.** No installation or restart occurred in this preflight.

## First attempt and correction

The frozen 16-member validation packet reproduced its recorded SHA-256, and
all four live predecessors plus seven candidate/`.new` absences matched the
reviewed card. Target execution then passed 50 tests and failed 22 before test
logic because the archive omitted
`evals/sysadmin-producer-fixture.json`, which two frozen modules load relative
to themselves. The temporary host and guest copies were removed immediately.
Production files retained their exact hashes, Aster Agent stayed on PID 25964
with zero restarts and no model request occurred.

The packet builder now includes exactly that regular, one-link fixture at its
required relative path and pins SHA-256
`aec7e2f140898d54c4d7ec8b9010a8faeb3e4191b90c3661f7e040dcc3207233`.
Builder tests now require 17 members, permit only this one nested member and
copy it into mutation/link negative tests. The corrected deterministic archive
is mode `0600`, 63,326 bytes, with SHA-256
`ff07c5086ee3e5c2dde04a152927fa8ef68417b0d9814faf1261b2ec56c5f322`.

## Passing target proof

The corrected archive was copied to a new root-owned Proxmox path, pushed to a
new root-only LXC104 directory and rehashed before extraction. Under
`/opt/aster-agent/venv/bin/python` with bytecode disabled and the candidate
directory ahead of `/opt/aster-agent`:

- all nine frozen `test_sysadmin_*.py` modules passed **72/72**;
- the candidate application imported both exact authenticated routes,
  `/v1/sysadmin/incidents/{incident_id}/propose` and
  `/v1/sysadmin/incidents/{incident_id}/observe`;
- no bytecode was written;
- all host and guest temporary copies were removed; and
- the four installed predecessors remained at their reviewed hashes.

Aster Agent remained active on PID 25964 with `NRestarts=0`. The accepted
llama/SYCL service remained active on PID 61089 with `NRestarts=0`; the shared
lease remained exactly ready. No incident, model request, service restart,
installed-file change, route activation, authority or repair effect occurred.

The exact seven-file release packet remains SHA-256
`b03586e9ee9bf59de0c94aa6e78afa832dc10a28169d718f4a85dc024d63bfcb`.
The only remaining release gate is the reviewed composite installation and
one Aster Agent restart. Automatic routing, observation execution and repair
authority remain closed.
