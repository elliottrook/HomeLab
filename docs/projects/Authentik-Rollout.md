# Authentik Service Rollout Project

> Status: Foundation proven; Milestone 2 rollout wave started — Forgejo done
> (native OIDC), Homepage and Beszel still open
>
> Project owner: Jason
>
> Last updated: 2026-08-31

## Purpose

Provide consistent, least-privilege browser authentication for suitable internal
services using Authentik and friendly HTTPS names while preserving direct,
private recovery access. This is a service-by-service rollout, not a bulk
conversion.

## Authoritative instructions

- [`docs/08-Authorization.md`](../08-Authorization.md) records the tested
  Authentik/Nginx Proxy Manager implementation and recovery details.
- [`docs/09-Service-Authorization-Onboarding.md`](../09-Service-Authorization-Onboarding.md)
  is the reusable native-OIDC, forward-auth and private-access procedure.

This project tracker controls sequence and completion. The runbooks control the
technical implementation.

## Inherited baseline

- [x] Authentik runs in LXC 106 at `192.168.50.22`.
- [x] Nginx Proxy Manager runs in LXC 107 at `192.168.50.23`.
- [x] `proxy.elliottrook.com` uses a valid wildcard certificate and tested
  Authentik password plus WebAuthn/passkey forward authentication.
- [x] Direct NPM administration remains available as a restricted fallback.
- [x] Both guests are monitored, backed up, mirrored and included in the
  encrypted recovery path.

## Scope and principles

- Prefer native OIDC/OAuth2 where the deployed application supports it safely.
- Use forward auth for suitable browser interfaces without dependable native
  SSO; retain the application's own login unless explicitly proven unnecessary.
- Create explicit Authentik groups and policies instead of granting every user
  access to every service.
- Keep internal DNS, certificate issuance and proxy configuration repeatable.
- Keep every direct management URL until the proxied path and rollback are
  validated.
- Keep services private to LAN/Tailscale unless public exposure is separately
  designed and approved.

## Never proxy through Authentik

Do not proxy SSH, DNS, SMB, NFS, iSCSI, RTSP, ONVIF, backup transports, the
Ollama API, the Tailscale control path or other non-browser protocols. Do not
make firewall recovery depend on Authentik or the reverse proxy.

## Milestone 1 — Identity and policy foundation

- [ ] Inventory intended users and define `homelab-admins`, family and any
  service-specific groups.
- [ ] Confirm at least two recoverable Authentik administrator methods.
- [ ] Define reusable allow/deny policy bindings and default-deny behaviour.
- [ ] Define naming, certificate, DNS and proxy-host conventions.
- [ ] Confirm WebAuthn/passkey enrollment and recovery for each administrator.
- [ ] Document the location and recovery process for secrets without storing
  their values in Git.
- [ ] Back up Authentik and NPM before the first rollout wave.

Completion gate: group, policy, DNS, TLS, recovery and rollback conventions are
documented and tested without changing another service.

## Milestone 2 — Low-risk rollout wave

Implement one service at a time using the onboarding worksheet and evidence
table in `docs/09-Service-Authorization-Onboarding.md`.

- [x] Forgejo — native OIDC via Authentik OAuth2/OpenID Provider, confirmed
  working end-to-end from a clean session (full password + passkey/MFA
  prompt). Local Forgejo administrator login retained as break-glass. See
  evidence log below for the two real bugs found and fixed along the way.
- [ ] Homepage — use forward auth and verify all dashboard/widget requests.
- [ ] Beszel — use native OIDC if supported; otherwise forward auth while agents
  continue using their direct private path.
- [ ] Confirm sign-in, sign-out, denial, direct fallback and rollback for each.
- [ ] Observe the completed wave before beginning the next one.

Completion gate: three lower-risk services work through friendly HTTPS names,
and losing Authentik/NPM does not prevent direct administrative recovery.

## Milestone 3 — Operations and application wave

- [ ] Portainer — prefer supported native OAuth/OIDC; keep a break-glass account.
- [ ] Pi-hole web interfaces — proxy browser UIs only; never proxy DNS traffic.
- [ ] Immich — validate native OIDC and mobile-client behaviour.
- [ ] Seerr and media-automation browser interfaces — preserve API keys and
  private service-to-service paths.
- [ ] Calibre and Audiobookshelf — test mobile reader/player behaviour.
- [ ] Jellyfin/Plex — proceed only if TV and mobile clients remain functional;
  retain native application authentication where appropriate.
- [ ] Update the service onboarding evidence table after every service.

Completion gate: selected applications have least-privilege access and every
non-browser client or integration continues to function.

## Milestone 4 — Infrastructure interfaces

Begin only after the lower-risk pattern has a stable observation record.

- [ ] Proxmox — use an OpenID Connect realm and preserve `root@pam` recovery.
- [ ] TrueNAS and Synology web interfaces — protect only the browser UI and
  retain storage/backup protocols on direct private paths.
- [ ] UniFi OS — preserve console and direct management recovery.
- [ ] Home Assistant — retain native authentication unless a reviewed OIDC path
  supports the web UI, mobile app and callbacks without weakening recovery.
- [ ] Keep OPNsense LAN/Tailscale-only unless a later security review explicitly
  approves proxying its web interface.
- [ ] Perform an Authentik/NPM outage drill and prove critical recovery paths.

Completion gate: protected infrastructure UIs remain recoverable during an
identity or reverse-proxy outage, and control-plane protocols are unaffected.

## Milestone 5 — Consolidation and operations

- [ ] Remove obsolete test providers, applications, DNS records and proxy hosts.
- [ ] Confirm certificate monitoring includes operationally important names.
- [ ] Verify Authentik and NPM backups after final configuration.
- [ ] Perform an isolated restore or other proportionate recovery validation.
- [ ] Update Homepage links only after friendly names are stable.
- [ ] Record the final service matrix, exceptions and accepted risks.
- [ ] Run HomeLab Doctor and a failure/rollback drill.

## Definition of done

The rollout is complete when every selected browser service has a documented
authentication decision, permitted users are enforced, client/API/control-plane
traffic remains functional, direct recovery paths are proven, and Authentik/NPM
backup and rollback procedures have passed.

## Evidence log

| Date | Service or milestone | Method | Result |
|---|---|---|---|
| 2026-08-22 | Nginx Proxy Manager | Authentik forward auth with password and passkey | Passed |
| 2026-08-24 | Project split | Rollout separated from initial-build record | Complete |
| 2026-08-25 | Authentik launch URL follow-up | Verified Base URL/outpost/NPM headers; replaced dashboard HTTP fallback link with `https://auth.elliottrook.com` | Passed |
| 2026-08-31 | Forgejo | Native OIDC via a dedicated Authentik OAuth2/OpenID Provider. Two real bugs were found and fixed, not just a straightforward setup: (1) Forgejo's actual OAuth callback path is case-sensitive to the Authentication Source name (`https://git.elliottrook.com/user/oauth2/Authentik/callback` with capital "A", matching what was typed into Forgejo) — the redirect URI initially registered in Authentik used lowercase and was rejected; confirmed the exact mismatch by capturing the live `authorize` request rather than guessing. (2) A known Gitea/Forgejo upstream bug: it cannot parse JWE-encrypted tokens, producing `oauth2: error decoding JWT token: jws: invalid token received, not all parts available` — fixed by clearing the Encryption Key field on the Authentik provider (token encryption must stay off for Forgejo specifically). Also corrected Forgejo's Additional Scopes from blank to `email profile` per the official Authentik-Forgejo integration guide. A separate, unrelated blocker was also found and fixed along the way: an OPNsense inter-VLAN firewall rule was missing, preventing Forgejo's host (192.168.20.30, Servers VLAN 20) from reaching NPM (192.168.50.23, Management VLAN 50) on port 443 at all — added a narrow pass rule scoped to just Forgejo's host. Validated with a full clean-session login (private window, no prior Authentik session) showing the complete password + passkey/MFA prompt. Also fixed an unrelated Homepage dashboard tile pointing at Forgejo's old IP-based URL instead of `https://git.elliottrook.com`. | Passed |
