# Pi-hole single-login preflight

Status: isolated proof complete; production cutover not performed.
Owner: Jason. Project: [Authentik rollout](../projects/Authentik-Rollout.md).

## Verified on 2026-09-26

The two installed Pi-hole images were exercised separately with synthetic
configuration and an empty gravity database. Neither test used production data,
credentials, networks, DNS ports or published HTTP ports. Each fixture used
Docker `network none`; its nginx guard shared that isolated network namespace.
The live container ID and start time remained unchanged. Test containers were
removed after each run.

| Host | Installed image | Result |
| --- | --- | --- |
| Primary, LXC 100 | 2026.05.0, `sha256:70a9c11171ded2eee735d88c127996da209284a329d50f5ae59c06b861d401b3` | 17/17 synthetic checks, including installed Homepage |
| Secondary, TrueNAS | 2026.07.2, `sha256:27b410ff85b3449158c1ed568b4078c6037463952ad9939b673b28ba13bd9aa7` | 16/16 synthetic checks |

The reproducible [proof script](../../scripts/authentik/pihole-isolated-proof.py)
uses only images already installed locally. Run on the primary with its default
`--installed-container pihole --homepage-container homepage`, or on TrueNAS with
`--installed-container ix-pihole-pihole-1`. It deliberately refuses occupied
fixture names. Its loopback peer addresses are synthetic test identities and
**must not be copied into production as an access policy**.

Passwordless Pi-hole accepts UI/API reads and a synthetic API write with a
foreign Origin. This is a prerequisite finding, not an assertion that browsers
will bypass every CORS or network control. The proposed guard denies missing or
wrong owner identity, a forged identity from the wrong actual TCP peer, foreign
Origin writes, writes without Origin and cross-site fetches. Same-origin owner
reads/writes work. A separate widget listener allows only summary reads from
its designated peer; configuration access, writes and other peers are denied.

## Consumer evidence

- Homepage primary widget uses v6 API at `192.168.20.20:8082`, with a file-backed
  application credential. Homepage is currently `172.18.0.2` on
  `homepage_default`; this address is observed, not a durable identity promise.
- [Homepage upstream handler](https://github.com/gethomepage/homepage/blob/main/src/widgets/pihole/proxy.js)
  fetches `GET /api/stats/summary` and supports requests without a key. The installed Homepage image
  `sha256:a0b71c8e757298d02560186bab9fbe3fc2d375c523a62cc1019177b37e48aa28`
  passed an isolated no-key widget request through the candidate statistics
  route; all four expected summary fields were present. Its live container
  ID/start time remained unchanged and the synthetic Homepage was removed.
- Read-only inspection of Home Assistant VM 103 found zero `pi_hole` config
  entries and no Pi-hole reference in configuration.yaml, automations.yaml or
  scripts.yaml. This does not cover arbitrary custom packages or external apps.
- Both persisted Pi-hole session tables were empty. This does not establish
  that no active or intermittent API clients exist.
- Doctor checks DNS resolution; these are not authenticated API consumers.
- Jason is unsure whether another phone app or script uses the API. Preserve
  that uncertainty in the cutover assessment; do not claim a complete inventory.

## Production design to finish

1. Keep DNS TCP/UDP 53, resolver configuration, gravity data and DHCP posture
   unchanged. Modify only one resolver at a time, with the other answering
   public and private queries throughout.
2. Make the real Pi-hole HTTP/API listener inaccessible to LAN clients and
   unrelated Docker peers. A host-only port mapping alone does not block direct
   Docker bridge access: use Pi-hole's web ACL or an equivalently verified
   private backend network. Inspect all IPv4/IPv6 listeners.
3. Use the existing NPM/Authentik owner gate. The host guard must require actual
   NPM source `192.168.50.23` plus NPM's overwritten verified `jason` header.
   Enforce each service's exact HTTPS Origin on state-changing methods; test
   browser settings saves, uploads and logout rather than assuming compatibility.
4. Give Homepage a separate statistics-only route with a durable, narrow
   source restriction. Remove its key from the widget only after proving the
   installed build works without it. Keep the protected credential for rollback.
   Do not allow Homepage unrestricted access to the passwordless API.
5. Prepare primary Compose and secondary TrueNAS-managed app changes using
   their actual configuration authorities. Do not replace the managed app with
   an ad hoc Docker container. The secondary's password environment setting
   overrides TOML; editing only the TOML is insufficient.
6. Before any live change, take verified protected config/database checkpoints
   and save exact old container/app settings and Homepage configuration. Prove
   a recovery route independent of Authentik/NPM, such as an authorized SSH
   tunnel into the private listener. Restore the old auth and access boundary
   together on rollback; never expose passwordless Pi-hole as a rollback step.
7. Test fresh passkey access, native UI operations, denied direct/spoofed access,
   origin checks, widget statistics, both DNS transports, all three internal
   resolvers, service restart persistence, and the second resolver's health.
   Extend the production boundary checker only after real ingress deployment.

Current result does not authorize claiming single-login completion. No live
Pi-hole password, app credential, port mapping, DNS data or NPM route changed.
