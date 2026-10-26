# M3 NLU complete-score failure inactive replacement card — 2026-10-25

> Decision: exact disabled installation approval required

## Purpose

Replace two inactive files in the staged LXC110 NLU calibration packet so a
timeout, endpoint error or transport uncertainty can never be certified and
scored as a complete calibration. This makes the downstream evidence boundary
match the already corrected runner and approved no-retry run card.

## Exact source and transaction

- source commit: `9f4da72d`;
- transaction:
  `scripts/aster-adaptive/install_nlu_calibration_score_boundary.sh`;
- transaction SHA-256:
  `bbb31643a35006912055f67253ab43663b9c8f1b90409dad9748ef88f381525c`;
- transaction test SHA-256:
  `8c07d6176df958980e61657ffceaf1149cf0e43c6d223b59a7aef22b4051e430`;
- local transaction tests: 2/2; and
- dependency-free NLU tests: 119/119.

The transaction replaces exactly these two files:

| Path under `/var/lib/aster-nlu-calibration/nlu-calibration-v1/` | Installed SHA-256 | Replacement SHA-256 |
|---|---|---|
| `nlu_calibration_score.py` | `ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd` | `7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd` |
| `nlu_calibration_journal.py` | `992960fe76540941fe9adf7b75ddaf82541c55039782bf4cf360ad6c5279a744` | `966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb` |

The stage validator and manifest are not members of the installed eleven-file
packet. They are hash-pinned temporary validation inputs only:

- validator `83c7ed1135e444d832518e95bc7df51c59d5cb1c3cc7041177f31fc8cb84c3c9`;
- manifest `7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80`.

## Preconditions and validation

Before replacement, require lease state `ready`, accepted llama active, exact
old hashes, root-only packet custody, no output, journal, bytecode cache or NLU
runner process. Preserve both old files in a new root-only checkpoint.

After replacement, require exact new hashes and root:root mode `0600`, validate
all eleven staged packet files, run the nine scorer regressions on target
Linux from a unique temporary test root containing the public development
fixture in the layout expected by the unchanged tests, import the
installed runner/scorer/journal without bytecode writes, and
repeat absence, llama and lease checks. Any failure restores both files
from the checkpoint and removes only bounded temporary transport files.

## Explicit exclusions

This does not start a lease, stop a service, call a model, create a run or
journal, score evidence, select a threshold, enable routing, arm a timer,
change F2, deploy the NLU or push Git. It is an inactive correctness upgrade.
