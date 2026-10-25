# M3 NLU calibration LXC110 staging boundary — 2026-10-25

> State: **OFFLINE PLAN COMPLETE — NO FILE STAGED**

## Read-only target preflight

The October 25 read-only check passed:

- `/var/lib/aster-nlu-calibration` is absent, so the proposed parent does not
  collide with prior evidence;
- LXC110 provides Python `3.13.5`;
- `/etc/aster-llama-api-keys` is `ollama:ollama`, mode `0600`, 325 bytes; its
  contents were not read;
- `aster-llama.service` is active; and
- `/var/lib` has 21,465,428 KiB available, far above the bounded packet and
  evidence size.

This proves placement feasibility only. Service idleness, exact runtime pins,
lease ownership, backup state and restoration budget remain fresh live gates.

## Purpose

The calibration runner must authenticate to the accepted local llama endpoint,
whose key remains in LXC110. Copying that key to the Mac would broaden secret
custody. Running from LXC110 instead requires a minimal, reversible staging
boundary for the private synthetic cases and content-free evidence.

## Fixed placement and custody

For one approved run, create exactly one fresh directory beneath
`/var/lib/aster-nlu-calibration/`, owned by root and mode `0700`. All staged
inputs and generated files are root-owned mode `0600`. Refuse an existing run
directory or any symlink. Do not use `/tmp` or `/run`, because a reboot could
erase the only evidence of an uncertain request.

Stage these exact inputs:

| File | SHA-256 |
|---|---|
| private `cases.json` | `6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e` |
| content-free `release.json` | `f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1` |
| `nlu-development-v1.json` | `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785` |
| `nlu_calibration_runner.py` | `b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11` |
| `nlu_calibration_corpus.py` | `3b383dcc181cc5c6a41d3aa9a30bc72ee30896ff0375bbc270de9bd82ba4f983` |
| `nlu_calibration_release.py` | `bdc93c7892eda067c0675c04259c996d6f43935ee84ba4ae6bbea6d1892488d9` |
| `nlu_calibration_score.py` | `ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd` |
| `nlu_calibration_journal.py` | `992960fe76540941fe9adf7b75ddaf82541c55039782bf4cf360ad6c5279a744` |
| `nlu_local_model_adapter.py` | `3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0` |
| `nlu_threshold_policy.py` | `984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d` |

The packet is also frozen in machine-readable fixture
`scripts/aster-adaptive/fixtures/nlu-calibration-stage-manifest-v1.json` at
SHA-256 `357b4e3d5514fe32b1509ac27f9eac3940edb0635db3a5008b4f29fc4f124a00`.
Validator `nlu_calibration_stage_manifest.py` at SHA-256
`8ea9daf47793aaeed0f2c475b4475cc1873173a9abc65089049e9c5bae86889e`
requires the exact paths, modes, endpoint, key location, ten inputs, two
outputs, exclusions and no-authority attestations. When invoked with all ten
`NAME=PATH` bindings, it rejects missing, changed, extra and symlink inputs and
hashes the opened regular-file descriptors. Its later
[staged-custody correction](M3-NLU-staged-custody-validator-boundary-2026-10-25.md)
also enforces the final root owner, `0700`/`0600` modes, exact ten-name set and
absence of output or journal files. The packet was added at local
commit `acaeeb079f3010ea3b3e0df21e3f63d9a906be24`; byte verification was added
at local commit `531c07fc02d77b36f0f27b9166f9e1b6c831681e`. The later
[llama response-envelope correction](M3-NLU-llama-response-envelope-compatibility-2026-10-25.md)
repinned the runner and manifest at commit `4a7adab5`.

Although the runner imports the score module for its fixed run schema, it does
not score inside LXC110. Do not stage `labels.json`, the policy-registration
artifact, threshold selector, holdout files, cloud credentials or tools.

## Source-packet validation

The [actual ten-file Mac source packet](M3-NLU-calibration-source-packet-validation-2026-10-25.md)
now passes the repinned byte verifier: 10/10 regular non-symlink inputs and
93,612 aggregate bytes matched the frozen manifest. This was read-only and did
not stage a file.

## Inactive staging split

The later [inactive staging card](M3-NLU-calibration-inactive-staging-card-2026-10-25.md)
separates the ten-file copy from model execution. A compatible lease is not
required merely to place and byte-verify an inert root-only packet while no
other host work is active. The fresh lease, idle endpoint, runtime pins and
restoration reserve remain mandatory before the first request. This reduces
exclusive-time setup without authorizing staging or inference by itself.

## Live execution sequence after separate approval

1. Require the exact staged packet and re-read size, mode, owner and SHA-256
   inside LXC110. Any mismatch is NO-GO and no model request follows.
2. Prove the compatible lease, quiet-host, backup and restoration gates from
   the main run card.
3. Invoke the runner once with distinct new `run.json` and
   `attempt-journal.jsonl` paths. Never retry an uncertain attempt.
4. Copy only those two content-free outputs to the existing owner-only Mac
   calibration custody directory. Verify source/destination hashes and modes.
5. Validate journal-to-run agreement and derive the score on the Mac using the
   existing private labels. Threshold selection follows only on a complete,
   valid 60-record run.
6. After verified Mac custody and a normal production postcheck, remove only
   this run directory. If any outcome is uncertain, leave it mode `0700` for
   reconciliation and do not clean or rerun.

## Exclusions

This plan does not authorize staging, deletion, a lease, service stop, model
call, threshold selection, holdout access, shadow collection, routing, egress,
tool use or production promotion. No live system changed while preparing it.

The focused runner/staging tests pass 21/21, and the complete dependency-free
NLU suite passes 115/115.
