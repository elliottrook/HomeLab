# M3 NLU Candidate-v8 development — 2026-10-26

Candidate-v8 is a development successor to rejected Candidate-v7. It uses only
public development data and calibration-v3 failure classes. It does not use or
open the independent holdout.

## Corrections

The system policy now states general rules for the measured v3 failures:

- deny a change that also destroys its only rollback or recovery copy;
- retain the relevant capability category on an ambiguous supported request;
- distinguish pure private-data publication from public research;
- ignore explicitly negated actions when assigning capabilities;
- map calendar schedules, other private records and local joins consistently;
- treat an explicit correction from change to inspection as read-only.

These are evaluation labels only. They grant no capability or authority.

## Sealed candidate

- Adapter SHA-256:
  `d40dc05c53d6c6d6f5ec012305a54e1c8b6b36732a214ada329a5978660b272c`
- Policy SHA-256:
  `6fcdb80ded087c138003d4ab9d4172617f465c90ff8f0325db3d48ae4126ce5e`
- Candidate artifact SHA-256:
  `033aa138e9995034d0ea19237f929e4dccab1c9341f0ff531e03ced84ac6d6a1`
- Candidate canonical bundle hash:
  `dfb770525603624c9bf7b834b9c99502eedd29aa86b3800e03135454895aaaaf`

The bundle remains local-only, tool-disabled, case-data-free and
`authority=not-granted`.

## Public development check

The bounded 24-case public-development run used the already-running accepted
llama/SYCL service without a restart:

- attempted: `24/24`
- structurally valid: `23/24`
- exact: `23/24`
- privacy underclassifications: `0`
- unsafe false routes: `0`
- result SHA-256:
  `f2369db314f55003f388c53f159fd96817a2cb8b9118833969ad0c551c570a3e`

The remaining public mismatch is the known structurally invalid
`change-ambiguous` response. Development is non-qualifying.

## Next gate

Candidate-v8 requires a new 60-case calibration-v4 created and blind-labelled
by separated roles, disjoint from development and calibrations v1–v3. V3 has
become development data for v8 and cannot qualify it. No threshold, holdout,
shadow promotion or automatic route may be created from this development run.
