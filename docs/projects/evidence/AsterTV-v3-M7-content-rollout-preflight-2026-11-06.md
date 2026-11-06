# AsterTV v3 M7 — content-state rollout preflight

Date: 2026-11-06

State: read-only preflight; rollout stopped before effects

## Verified predecessor state

- Aster Agent LXC 104 identified as `hermesagent`; `aster-agent` is active with
  zero systemd restarts. Its live gateway hash is the accepted predecessor
  `f2780775df560903ecf6a0b4efe224343f327914bd680fe8fdd4abb24484e983`.
- Home Assistant VM 103 responds through its guest agent. Core 2026.9.1 is
  running; no update was attempted. Its bridge and contract hashes are the
  accepted predecessors `213a813d…95fac` and `ea42ebed…434f`.
- Bedroom identified as `AsterTV-Bedroom`; Kodi is active, JSON-RPC reported no
  active player and the Remote client hash is the accepted predecessor
  `c28bf36e…a5d49`. The Remote apply oneshot is correctly inactive after boot.

These versions are compatible with the repository candidate's gateway-first
rollout and its explicit predecessor fallbacks. No key, configuration, package,
service or display changed during these checks.

## Family identity stop

Family's address still resolves at `192.168.1.157` to the independently
recorded Ethernet MAC `84:47:09:a1:d3:55`. SSH presents Ed25519 fingerprint
`SHA256:qup6j5SaoLYSgeUyrMbXMD2+lpd+DGupbgO6DkHxhm8`, but that public key is
not present in the Mac's current or retained known-hosts files and the prior
evidence did not record its fingerprint value. Strict host-key checking
therefore denied access. The key was inspected but not accepted, and no
`StrictHostKeyChecking=no` bypass was used.

Family must remain untouched until the owner accepts that key after the MAC/
hostname/device identity is rechecked. Once accepted, the public fingerprint
should be recorded in fleet identity metadata so future agents can distinguish
a reinstall from an impersonation rather than rediscovering the gap.

## Remaining effect gate

Before deployment, require:

1. explicit acceptance and pinning of the Family public SSH fingerprint;
2. fresh no-active-player checks and owner confirmation that both displays are
   free;
3. exact Aster Agent, Home Assistant, Family and Bedroom checkpoints;
4. gateway-first deployment, then Home Assistant, then clients;
5. content-state freshness/replay/absence-of-history proof while leaving volume
   policy inert; and
6. Remote, Family equipment, Dolby/HDR and Bedroom stereo regression checks,
   with exact rollback on any failure.
