# M1/D4 fixed Doctor activation result

**Date:** 2026-10-25  
**Result:** PASS after one pre-effect fail-closed correction  
**Source:** `122b566164ee923bc227dc9b95c423b6e1db6c06`  
**Activation script SHA-256:** `1dbfadd48df75565851df0d620f10e80f4c9805eea44df037afad3b2c93df440`

## Measured result

The first approved activation candidate stopped at its initial registered-client
health precondition because an embedded JSON bytes literal was over-escaped.
It stopped before checkpoint creation, database enrollment, service enablement
or a fixed request. Independent postchecks found both fixed units disabled and
inactive, five fixed database counts at zero, SQLite integrity `ok`, normal
broker/Aster active with zero restarts, and no activation checkpoint.

The corrected candidate added an executable compile check for that embedded
health source. Its exact health probe passed live as `hlabagent`; shell/hash
checks, 3/3 activation tests, 15/15 fixed-Doctor tests and 39/39 broker tests
passed, and the platform owner returned GO. Jason approved the exact retry.

The retry then passed all bounded steps:

- enrolled UID 978 only as `agent-aster-fixed-doctor` in `observer` state;
- created only service `aster-fixed-doctor`, capability
  `diagnostic.aster-inference.latest`, and one Green, non-probationary grant;
- enabled and started only the dedicated gateway and caller units;
- completed exactly one fixed request with status `consumed`;
- accepted only schema 1, source `homelab-doctor-structured/v2`, state `ok`,
  the allowlisted `aster.agent_inference` check ID and bounded age;
- retained broker/Aster and both dedicated services active with zero restarts;
- retained SQLite integrity `ok` and the Forgejo project-document route as
  Yellow, non-probationary and enabled;
- created the root-only rollback checkpoint at
  `/root/aster-fixed-doctor-activation-pre-20261025T1845PDT` with directory
  mode `0700` and database/checksum files mode `0600`.

The normal broker socket remains `hlabroker:hlabroker-clients` mode `0660`.
The gateway socket is `aster:aster-lab-broker` mode `0660`; the dedicated
caller socket is `aster-doctor-caller:aster-doctor-client` mode `0660`.

## Boundary retained

No model call, ordinary Aster route, Forgejo write, Companion change,
credential access, schedule change, B60/lab/F2/F6 action or production
inference restart occurred. This proves the fixed read-only authority path; it
does not prove diagnostic usefulness or authorize a broader tool class.

## Next gate

Exercise the fixed path only through a preregistered usefulness evaluation that
keeps the model route and any broader authority separately gated. Preserve the
single-purpose observer/grant and do not convert this result into generic shell,
Doctor-text or repair authority.
