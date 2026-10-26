# M3 NLU final-attempt completion inactive replacement card — 2026-10-25

State: **READY FOR ONE EXACT INACTIVE INSTALLATION DECISION**

Source commits:

- behavior correction and frozen packet: `0e4b7311`;
- transaction and tests: full commit
  `07baddcac0f1cfc45eb2a4d24ee7ceb908f1130c`.

## Decision value

Replace only the superseded, unexecuted LXC110 calibration runner so a
transport or engine failure on the final case cannot be reported as a complete
run. This is required before any calibration execution can be considered.

## Exact inputs

| Input | SHA-256 |
|---|---|
| `nlu_calibration_runner.py` | `88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0` |
| `nlu_calibration_stage_manifest.py` | `215e221165fafcacb43ccae7230c0cad13a6e19ca9e41ccab9e019f815dc42e5` |
| `nlu-calibration-stage-manifest-v1.json` | `835bcb55ba93d25427b322c6cf93aee06cba1b5e7221af7fb63dbd41d1aab114` |
| `test_nlu_calibration_runner.py` | `c9bdc21bafd9bfcdc263c56addd12c29fa88a5bd3ef23ab4c85d04d18c3b555d` |
| transaction | `7995d6ef6fd413797cd22483876b71db72881e705bd9c501ececd83c8bd9493d` |
| transaction tests | `9ccc27ef49b74319f930b7562eeb0162591a55ffef83f42e8de1cc1c85d8f017` |

Expected predecessor at
`/var/lib/aster-nlu-calibration/nlu-calibration-v1/nlu_calibration_runner.py`:
`a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f`.

## Transaction

Run `scripts/aster-adaptive/install_nlu_calibration_completion_correction.sh`
once from Proxmox after copying the four pinned temporary inputs to the exact
`/tmp` names in the script. It must:

1. require lease state `ready`, active llama service, the exact predecessor,
   exact eleven-file packet, no runner process, and no output, journal or cache;
2. preserve the predecessor in a new root-only checkpoint;
3. atomically replace only `nlu_calibration_runner.py` as root:root mode `0600`;
4. validate the full staged directory against the corrected manifest;
5. run all 17 runner regressions and the import check on target Linux with
   bytecode writes disabled;
6. recheck no process/output/journal/cache, active llama and ready lease; and
7. remove all temporary transport files.

Any failure restores the exact predecessor and reports the retained checkpoint.
The script does not delete the checkpoint or use recursive removal.

## Explicit exclusions

This change does not acquire a lease, start or stop a service, invoke the
runner, read the key, call a model, create output or a journal, select a
threshold, access the holdout, enable routing, change F2 timers or push Git.
The installed candidate remains inactive after success.

## Acceptance

Pass only if every hash/custody check, manifest validation, 17 target-Linux
tests, import and absence/health postcheck succeeds. Record the checkpoint and
installed runner/manifest hashes. Failure means the old inert packet remains
and calibration stays blocked; do not retry an uncertain transaction.
