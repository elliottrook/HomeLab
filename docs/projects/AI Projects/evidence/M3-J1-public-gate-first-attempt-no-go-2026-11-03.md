# M3 J1 public gate first attempt — 2026-11-03

## Decision

**NO-GO; ZERO CASES PROJECTED; NO RETRY.**

Jason approved one bounded execution of the frozen J1 public gate. The command
failed during input identity validation, before the classifier was loaded or
any public case was projected. No result file was created.

## Exact failure

- first failure phase: `input-identity`
- failure class: `PUBLIC_FIXTURE_PATH_MISMATCH`
- expected fixture digest: `1565a21c…3785`
- supplied file digest: `6d67a95d…bdbb`
- artifact file digest: `7153f630…ba5e` (matched)
- execution receipt digest: `d769d2a1…d5df` (matched)
- projected cases: 0
- output files: 0
- network/model calls: 0
- holdout reads: 0
- authority: not granted
- automatic routing: off

The supplied path named the release manifest
`nlu-j1-public-gate-release-v1.json`, not the frozen 24-case public fixture.
The actual repository fixture `nlu-development-v1.json` still matches the
frozen digest `1565a21c…3785`. This is a deterministic packet/launch-path defect,
not a classifier result.

## Mitigation

The focused test suite now verifies the real repository fixture against the
runner's frozen digest. The spent approval is not reused. A corrected packet
must name the exact fixture path, pass the complete focused suite and receive a
fresh one-time effect decision before another attempt. The sealed holdout,
deployment, routing and tool authority remain closed.
