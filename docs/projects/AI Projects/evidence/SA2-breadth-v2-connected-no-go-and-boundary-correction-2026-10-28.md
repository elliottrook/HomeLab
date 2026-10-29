# SA2 breadth v2 connected NO-GO and boundary correction — 2026-10-28

## Result

The corrected SA2 breadth v2 publisher is installed and its evidence transaction
is coherent. A fresh Doctor publication produced one aggregate and two sidecars
with the same run identifier, generation time and digests. The four installed
unprivileged readers returned the expected bounded states:

- NetBox network inventory: `ok`, 23 devices, 22 virtual machines, one site,
  one rack, seven VLANs and seven prefixes;
- Aster gateway public configuration identity: `ok`;
- typed backup protection catalogue: `fail`, matching the fresh Doctor report;
- sanitized gateway priority-0–3 journal aggregate: `ok`, zero events in the
  fixed 900-second window.

The first connected four-source investigation nevertheless failed closed before
accepting its first follow-up. No proposal was journaled, no producer ran, and no
authority or effect was granted. The retained diagnostic response showed the
cause: the hypothesis described the **fixed public configuration identity**.
The boundary treated the adjective `fixed` as a claim that a repair had already
been performed.

This is a proposal-boundary false positive, separate from the v1 publication
race. Retrying the unchanged installed boundary would be unreliable, so the
live connected gate remains NO-GO.

## Corrected candidate

The correction keeps the existing completed-effect deny list and adds two narrow
context rules:

1. explicit `not`/`never` wording around a denied verb is accepted as a
   non-action statement;
2. `fixed` is accepted only when it directly describes one of the registered
   immutable evidence nouns, such as a fixed public configuration identity or
   report.

Positive claims still fail closed. Tests explicitly reject both “the service
was restarted” after a negated check and “not only restarted but also fixed.”

Exact candidate files:

| File | SHA-256 |
|---|---|
| `services/aster-agent/sysadmin_proposal_boundary.py` | `af450ad30aa2136b92a5994fccb376e5958e34a7da7bb6c59c6795c9aad5b956` |
| `services/aster-agent/test_sysadmin_proposal_boundary.py` | `766241a2edc1cc876972034a64d6479142634ec19be493d9f0f85f11ee7a9d2c` |

The current installed predecessor is root-owned mode `0644` at
`/opt/aster-agent/sysadmin_proposal_boundary.py`, SHA-256
`2050cd7e12b5207dce21c5087d4e643ffa85965376d415c0ed7ee673d9894515`.

## Validation

- all 86 local `test_sysadmin_*.py` tests pass;
- all 14 proposal-boundary tests pass with the candidate first on LXC104's
  Python path, without changing the installed file;
- the same temporary candidate completed the full installed four-source loop:
  four decisions, three consumed observations, terminal `complete`, exact
  NetBox/config/backup/log source set, authority `none`, effect `none`, and
  healthy idle postcheck;
- the backup failure remained a diagnosis only and no repair was implied;
- Aster Agent remained active at PID `29852`, restart count zero;
- accepted llama.cpp/SYCL remained active at PID `61089`, restart count zero;
- the whole-host lease remained `ready`.

The temporary-path result proves the corrected candidate against the live
installed sources. It does not change production and is not a release by itself.

## Exact bounded live change

The next change replaces only
`/opt/aster-agent/sysadmin_proposal_boundary.py` after preserving the current
file in a new root-owned checkpoint, verifies the installed hash, and restarts
only `aster-agent.service` once. It then runs the same four-source no-effect
connected investigation once and performs production postchecks. On any install,
restart, connected-check or postcheck failure, restore the preserved predecessor,
restart Aster Agent once, and retain the failed evidence.

This change does not restart or change the model, change routing, grant tools,
run a repair, alter the publisher/timer, change the Companion, or affect Lab
Hours. The Aster restart is the sole new effect requiring approval.

