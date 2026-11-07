# AsterTV v3 M7 — Family content-gateway correction

Date: 2026-11-06  
State: repository candidate; no live effect

## Outcome

The disabled Family volume freeze correctly included the new Kodi session
publisher and Home Assistant controller, but its Family composition still
packaged the accepted standby/equipment gateway. That predecessor cannot
accept or expose content state, so the ordered gateway-first rollout would
have stopped at its first transport check. The release tests caught the
composition change once the missing gateway payload was added; no appliance
or service had been changed.

The materializer now derives a Family-specific gateway from two immutable
inputs:

- accepted Family standby/equipment predecessor
  `a064cfc5ea275e2f28c3c5d8e98cb2e3743a9a284ffe08760d91913304bb8518`;
- reviewed shared content-transport candidate
  `3ad1f24ff56aee121dbd26e997f93af618e6c8f085417f95a22fdc414c0d222d`.

The derived payload is
`715b172a62e978ccaf79dfd3f9801da641cd067da72ad7187658efa9ccc0d73a`.
Its diff from the accepted Family predecessor is limited to the content-free
state model, replay/freshness validation, current-state retention and the
equipment-scoped content read route. The shared candidate's unrelated speech
default is explicitly removed, so Family retains the accepted internal voice
route. Hash and normalization anchors fail closed on either input changing.

## Read-only live audit

- Family's freshly scanned ED25519 key reproduced the pinned fingerprint
  `SHA256:qup6j5SaoLYSgeUyrMbXMD2+lpd+DGupbgO6DkHxhm8`; an isolated temporary
  trust file was used and the persistent trust store was not changed.
- `AsterTV-Family` reports Kodi active with zero restarts and zero active
  players. Its installed Remote service remains the accepted predecessor
  `a8b26f93425e5f17cdfdb3348fd4adca1e711c0c976b8eab2fc8baab8c3709b8`;
  the new session helper is absent, as expected before rollout.
- Aster Agent is active with zero restarts and gateway
  `a064cfc5…8518`.
- Home Assistant Core 2026.9.1 passes `ha core check`. Its installed bridge and
  contract remain `213a813d…95fac` and `ea42ebed…434f`; the content-policy
  module is absent, as expected.

## Candidate verification

- Derived gateway parses as Python and retains the accepted voice default.
- 20 Home Assistant policy/component/contract tests pass.
- 38 Kodi client/session/installer tests pass.
- All 53 fleet/materialization/release tests pass against the superseding
  immutable freeze.
- Verified Family release outputs are composition `a09ef2b5…9411`, bundle
  `5eb17b3f…feed`, plan `f47481ab…2661`, guard `96040595…3f14` and SBOM
  `6d88bafd…d477`.

The Mac package index could not supply the repository's pinned future FastAPI
version for a fresh isolated dynamic gateway replay. The shared gateway
candidate already passed its pinned-environment tests; a new pinned Aster
runtime replay remains mandatory immediately before any live deployment.

## Remaining effect gate

Do not install from this record. First issue a superseding immutable freeze,
then replay the gateway tests in Aster's pinned environment. A live rollout
still requires idle-display confirmation, exact checkpoints, gateway-first
installation, Home Assistant second, Family client last, and content
freshness/replay/no-history proof while the volume profile remains disabled.

