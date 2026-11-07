# AsterTV v3 M11 post-acceptance reconciliation — 2026-11-06

## Outcome

The repository candidate remains reproducible after the accepted Family and
Bedroom M7 work. Two independent builds from commit
`b2781022fe8b3d54a67d45cdef8bbf0e36a94e43` produced identical plans, guards,
SBOMs and bundles. Their hashes exactly match the later immutable
`astertv-v3-rc1-family-content-gateway-candidate-2026-11-06` record, so the
historical RC1 and its amendments were not rewritten.

The integrated local gate reports `pass-with-owner-acceptance-open`:

- 76 local test files pass;
- 93 files pass the secret-pattern scan;
- 15 pages expose 127 focus controls with zero conformance failures;
- Doctor, Beszel, NetBox, wiki/reference/mirror and recovery readiness have
  zero gaps; and
- the connected Jen HEVC, gateway, live-recovery, operations and performance
  gates pass.

The only integrated gate still open is the non-author physical walkthrough.

## Reproduced candidate

| Device | Composition | Bundle | Result |
| --- | --- | --- | --- |
| Bedroom | `eab64fd2…9bb3b7` | `212ab281…8f7437` | reproducible; full-composition deployment/soak still open |
| Family | `a09ef2b5…a79411` | `5eb17b3f…1efeed` | reproducible; explicit final promotion still open |
| Jen | `34cccf84…a010ec` | `45ba989d…9da5f` | reproducible standing canary |
| Guest | `5ca63262…82339e` | `4d79b20a…201e0` | reproducible and deliberately non-deployable |

All plan, guard and SBOM hashes also match the immutable candidate record.
Guest remains fail-closed with the sole blocker `candidate-not-deployable`.

## Accepted since the original freeze

- Family physical equipment controls, AsterTV soft standby and the selected
  content-volume profile are deployed and owner-accepted.
- Family content state, playback/class transport, bounded volume automation,
  manual override, outage/restart behavior and Dolby Atmos passthrough are
  accepted.
- Bedroom now publishes identity-free content state through an empty-action,
  no-volume-authority route. A bounded movie proved idle → playing/Movie →
  idle with zero recorder history and no Kodi/Aster restart.

These accepted slices do not mean the complete Bedroom composition is
deployed. The bounded Bedroom rollout intentionally omitted the unused
equipment helper and retained a narrower live manifest. That expected gap is
documented rather than silently filled.

## Remaining boundaries

Repository automation cannot close these items:

1. Bedroom physical Volume Down/Up, Mute and Power observation through the LG
   ARC/eARC SIMPLINK/CEC chain, including physical recovery and audio-equipment
   inventory.
2. Bedroom listening-level selection and content-volume safety acceptance.
3. The non-author physical walkthrough plus full Bedroom composition rollout,
   reboot and normal-use soak.
4. Explicit final Family promotion while idle, followed by the Family
   production-path acceptance run.
5. The external Media Lifecycle replacement-view/identity handoff. Until it
   arrives, the four exact v2 smart-playlist routes remain the accepted
   fallback.
6. Final user handover, intent/efficiency review and project close-out.

No live client, Home Assistant service, gateway, firewall, account, credential
or media state changed during this reconciliation.

Machine-readable receipt:
`services/kodi/astertv-fleet/releases/astertv-v3-m11-post-acceptance-reconciliation-2026-11-06.json`.
