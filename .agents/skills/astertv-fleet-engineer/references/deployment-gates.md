# AsterTV deployment gates

## Required before effects

- exact hostname/device identity matches the desired manifest;
- playback is idle and the user has released the display when interactive
  validation will move it;
- accepted predecessor and named recovery checkpoint exist and hash correctly;
- immutable release artifact is present and its SHA-256 matches Forgejo;
- target composition, dependencies, compatibility, SBOM and performance gates
  pass;
- the planned diff contains only declared owners/resources;
- credentials remain source-local and required network changes are exact;
- rollback can operate without the wiki or Aster services; and
- current authorization covers the effect. A remote push always needs its own
  immediate confirmation under repository policy.

## Stop conditions

Stop on identity ambiguity, active playback, unexpected files/settings,
dependency loss outside the plan, secret output, checkpoint failure, broader
firewall/DNS/DHCP scope, irreversible peripheral state, or any regression in an
unchanged workflow.

## Promotion order

For global changes, validate synthetic fixtures, then Jen, then Bedroom, then
Family. Bedroom must retain stereo/Wi-Fi behavior. Family must retain measured
Dolby/HDR and equipment control. Do not infer fleet limits from Jen.

## Completion evidence

Capture composition hash, artifact hash, checkpoint, changed owners/resources,
tests, physical observations, allow/deny network results, rollback result, and
the exact next action. A successful installation is not owner acceptance.
