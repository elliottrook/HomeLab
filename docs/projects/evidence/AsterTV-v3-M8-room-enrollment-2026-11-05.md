# AsterTV v3 M8 — Family and Bedroom Remote enrollment

Date: 2026-11-05  
Scope: additive Aster Remote clients for AsterTV Family and AsterTV Bedroom

## Outcome

The existing Jen pilot was preserved and the Remote gateway now has three
independently revocable identities and owner-authorized rooms: `jen-lab`,
`family`, and `bedroom`. Family and Bedroom each run the same outbound-only,
semantic Kodi service. No inbound client listener, equipment authority,
volume/mute/power action, firewall rule, DNS record, certificate, browser
credential, or playback state changed.

## Recovery points

- Gateway accepted checkpoint:
  `/var/lib/aster/checkpoints/astertv-v3-m8-rooms-20261105-r3`
- Family checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m8-remote-astertv-family`
- Bedroom checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m8-remote-astertv-bedroom`
- Gateway attempts `…-20261105` and `…-20261105-r2` failed only their
  validation harness and restored the original Jen-only environment exactly.
  The accepted retry corrected the long-poll timeout and bound-address checks.

## Validation

- Aster Agent is active and its sanitized environment contains exactly Jen,
  Family, and Bedroom with distinct room IDs and non-empty private keys.
- The gateway showed four established TCP 9120 sessions during validation;
  both new Kodi services were enabled and polling, while Kodi remained idle.
- Family and Bedroom identity and key files are mode `0600`.
- Both add-ons report enabled through Kodi JSON-RPC; neither box had active
  playback after installation.
- All transient client, Proxmox, LXC, and staging credential files were
  removed after acceptance.
- The local focused suite covers additive preservation, identity boundaries,
  idle/recovery guards, manifest reapply, semantic-only actions, and the real
  20-second empty-poll response.

## Remaining acceptance

Use the live iPhone Remote room selector to choose Family and Bedroom and run
one harmless Home or directional action on each. Equipment buttons remain
disabled until M7 supplies explicit room-equipment authority.
