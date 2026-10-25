# Recovery pin diagnosis and NLU acceptance receipt — 2026-10-25

Received Adaptive `c21a8bda451b6d21446011e092d3226c161ffdfa` after a fresh
Forgejo fetch. Platform remains `6fb0207fec5190e0c34ed3bc72ea38e128f06127`;
the published B60 base before this response is
`1672ef5b10b65d117db050ed0fc901c18a1757e3`. This is a source/document
receipt, not a new live host inspection or acknowledgment by the other owner.

## F2: specific failure identified, not a successful archive test

The owner's October 25 terminal record reports `FINAL_GUARD_INSTALLED_PIN`,
prepare success, no scanner/result rows and healthy production postchecks.
The subsequent correction receipt identifies stale `host_exclusion.py` pins
in the fixed wrapper and observer. Jason approved a two-file correction,
with 17/17 target-Linux checks and retained rollback. Installed identities
reported by the independently checked receipt are:

- wrapper `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34`;
- observer `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858`;
- exclusion helper `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61`.

The exact evidence path under `docs/projects/AI Projects/evidence/` is
`F2-host-exclusion-pin-correction-and-october-26-review-2026-10-25.md`, SHA-256
`a8a5043bb92f0d62b3599f3f23707347609f72da9b327134f259936e62dff530`.
It records October 26 one-shot prepare/final timers at 01:15/01:20 PDT already
approved and activated, plus an observation-only 01:42 reconciliation. F2
remains open pending three valid exit-zero archive rows. No additional owner
approval is currently holding up that scheduled attempt.

This diagnoses the October 25 refusal, not every previous failed cycle.
It does not remove the independent launcher process-contract concern: the
receipt keeps coordinator `9efe6e5d…e8a1`, whose wrong default B60 observed.
No evidence of that default's correction or new fetchable platform source is
published on the owning ref. Preserve the existing request; do not overwrite
the live files, loosen checks or duplicate the timed owner.

## NLU: accepted constraints now exist for this lane

Read the new acceptance and candidate-seal records. Exact paths under the
same evidence directory:

- `M3-NLU-owner-policy-acceptance-2026-10-25.md`, SHA-256
  `55536d7e7e35ef8697feb2e49175de909957a4caa5f6c1a8b789db34445b495a`;
- `M3-NLU-local-candidate-seal-2026-10-25.md`, SHA-256
  `46ac79295449bdf5b1a5096340d2183ec0016ae0d8d29e21e3e911b7bec8d69e`.

Adaptive records Jason's exact initial **NLU calibration** acceptance: zero
privacy underclassification and unsafe false routes, at most 10% selective
error, at least 60% coverage, 60+ calibration cases and 10+ per family.
These are no longer mere example constraints. They do not become the A1
answer-quality thresholds or its useful-answer latency budget. B60 does not
create a second policy or infer routing, tool or deployment authority.

The accepted production 9B/SYCL stack is sealed as an evaluation candidate,
bundle `2245879f287bb58c502ae178c6e244edf98d29371b296c8ceee4881acc79f00c`.
This is not a promotion or a passed calibration. Later custody/scoring-release
records exist on the same ref; this review did not read private cases/labels,
verify human role independence, run calibration or claim holdout success.
The separate D4 candidate-G record confirms no compatible live lease was
available; its approved model attempt remains unspent, not executed by B60.

## Independent exact-peer offline validation

Exported `scripts/aster-adaptive` from the exact Adaptive commit into a new
disposable directory. Ran only these six no-network suites on the existing
Python 3.9.6 interpreter, without installing a package:

`test_nlu_threshold_policy`, `test_nlu_threshold_selection`,
`test_nlu_holdout_release`, `test_nlu_candidate_bundle`,
`test_nlu_policy_acceptance`, `test_nlu_policy_registration`.

Result: **54/54 pass**. This supersedes the earlier 26-test subset for these
updated modules; do not add the counts as independent quality observations.
Source SHA-256 pins, under `scripts/aster-adaptive/`:

| Module | SHA-256 |
|---|---|
| `nlu_threshold_policy.py` | `984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d` |
| `nlu_threshold_selection.py` | `9edc0317fe655bfc49b888d755155393cdc468e11bccc27dbe4881b886922cbb` |
| `nlu_holdout_release.py` | `6a0f5a9846064b74665434d415e69d314ce230f150b7f3d684619961fe89f7cc` |
| `nlu_candidate_bundle.py` | `5a797b2f0166d6ead276c0487887074ea1f78396d2ddfcd4ea7d6915df36e156` |
| `nlu_policy_acceptance.py` | `304e5b6870ca8dfcbfa140d959e95edd802f9cdb1678a4690969d7d2c7e944d7` |
| `nlu_policy_registration.py` | `1fecc563781b3b7f09a5a5415d691ba24dba7e7a87471ec4c64721d3e521f218` |

No NLU runtime/scorer model call or broad adapter suite was run. No production
probe, scan, lease, service/timer, configuration, credential, download, mount
or package action occurred. Continue against actual owner formats and consume
the next terminal result; full recovery and A1 admission still gate B60 trials.
