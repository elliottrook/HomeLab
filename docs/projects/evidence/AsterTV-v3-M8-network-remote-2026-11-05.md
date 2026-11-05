# AsterTV v3 M8 network-authorized Remote — 2026-11-05

## Outcome

The Aster Remote PWA now opens immediately on the authorized household LAN
without an Authentik interaction. This is not an unauthenticated public route:
the hostname remains private split DNS, Aster Agent accepts browser requests
only from the trusted Nginx address, and Nginx's single client address must
match an explicit subnet-to-room map.

The existing Bedroom, Family and Jen television clients retain separate
outbound poll keys. Exact Origin validation, semantic actions, bounded queues,
expiry, idempotency and rate limits are unchanged. The browser receives no
Kodi or speech credential. Voice uploads traverse the same-origin gateway,
which uses a dedicated STT-only key; the speech TTS dependency rejects it.

## Guest preparation

Guest VLAN `192.168.40.0/24` maps only to future room ID `guest`. Because that
room is not enrolled, the route fails closed. No Guest firewall or DNS change
was made. The fourth box requires a new independently revocable client identity
and a separately reviewed narrow Guest-to-Nginx TCP 443 rule. It must not
expose any household room or direct internal service.

The same PWA is the Android answer: Chrome **Add to Home screen** / **Install
app**. There is no separate native package or duplicated control policy.

## Evidence

- Authoritative Lab Hours checks were clear for the speech restart and recovery
  window.
- Gateway pinned environment: 8 protocol/security tests pass.
- Speech pinned environment: 25 tests pass, including STT-only key isolation.
- Local static/installer suite: 20 tests pass; JavaScript/Python syntax and
  whitespace checks pass.
- Trusted HTTPS session: HTTP 200 with exactly `bedroom`, `family`, `jen-lab`.
- Direct gateway session: HTTP 403.
- Direct request with a forged Guest forwarded address: HTTP 403.
- Aster Agent and Aster Speech are active; all three existing clients report
  connected.

## Recovery

- Gateway: `/var/lib/aster/checkpoints/remote-network-auth-20261105`
- Speech: `/var/lib/aster-speech/checkpoints/remote-network-auth-20261105`

No television restart or client mutation was required.
