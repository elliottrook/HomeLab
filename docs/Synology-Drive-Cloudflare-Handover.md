# Synology Drive Cloudflare Sharing Handover

> Status: operational and externally validated  
> Completed: 2026-08-26  
> Primary project: [Synology Drive Family Cloud](projects/Synology-Drive-Family-Cloud.md)

## Outcome

Synology Drive sharing is available at `https://share.elliottrook.com` through a Cloudflare Tunnel. No inbound WAN port was opened. Synology Drive now generates HTTPS sharing links with that hostname, and a real public image share returned HTTP 200 from an unsigned external request through Cloudflare.

## Architecture

| Component | Address / identifier | Role |
|---|---|---|
| Main Synology (GoWest) | `192.168.20.41`, Servers VLAN 20 | DSM 7.4.1-90080 and Synology Drive 4.0.3-27892 |
| Reverse-proxy LXC 107 | `192.168.50.23`, Management VLAN 50 | Runs the Cloudflare connector in Docker |
| Proxmox | `192.168.50.10` | Hosts LXC 107 |
| OPNsense | `192.168.1.1` | Inter-VLAN firewall authority |
| Public hostname | `share.elliottrook.com` | Cloudflare-published Drive/DSM HTTPS endpoint |
| Tunnel | `synology-drive-share` / `f6cfcbd3-b1ba-48c5-b2fc-27592880238b` | Outbound-only Cloudflare Tunnel |

Traffic path:

`Internet -> Cloudflare -> cloudflared LXC 107 -> NAS 192.168.20.41:5001`

## Changes made

### OPNsense

Added and applied a Management-interface pass rule:

- source: `192.168.50.23`
- destination: `192.168.20.41`
- protocol/port: TCP `5001`
- description: `Allow cloudflared LXC to Synology DSM HTTPS for Drive sharing`
- ordering: above `Block Management Access to the Internal Network`

No WAN NAT or port-forward rule was added.

### Synology firewall

The active default-deny profile now permits `192.168.50.23 -> TCP 5001`. The unrelated existing `172.20.0.3 -> TCP 2283` rule was preserved. The rule was imported with Synology's supported `synofirewall --import` flow and verified in the generated IPv4 firewall rules.

A pre-change firewall export and the modified profile were retained in the Codex task workspace, not committed to Git:

- `work/synology-firewall-backup-2026-08-26.json`
- `work/synology-firewall-drive-2026-08-26.json`

### Cloudflare connector

LXC 107 runs the official `cloudflare/cloudflared:latest` image with Docker Compose:

- compose file: `/opt/cloudflared/compose.yml`
- token environment file: `/opt/cloudflared/.env`
- restart policy: `unless-stopped`
- four QUIC connections registered during validation

The token is intentionally absent from this repository. Recover or rotate it only through the Cloudflare dashboard.

Published route:

- hostname: `share.elliottrook.com`
- service: `https://192.168.20.41:5001`
- Origin Server Name: `elliottrook.familyds.com`
- origin TLS verification: enabled
- Cloudflare Access: not enabled

The Origin Server Name matches the NAS certificate while the public client certificate is issued and served by Cloudflare.

### Synology Drive

In Drive Admin Console -> Settings -> Sharing -> Customize Sharing Link:

- Force HTTPS: enabled
- sharing-link customization: enabled
- domain type: Customized
- customized domain: `https://share.elliottrook.com`

## Validation evidence

- LXC 107 successfully connected to `192.168.20.41:5001`.
- Cloudflare Tunnel registered four healthy QUIC connections.
- Public DNS resolves `share.elliottrook.com` to Cloudflare.
- The public hostname returned HTTP 200 with `server: cloudflare`.
- DSM and Synology Drive loaded successfully through the hostname.
- A public link for `HDR Window.jpeg` was generated with the custom hostname.
- An unsigned external request to that share returned HTTP 200.

The public test share URL is deliberately not stored in Git because it contains a live capability token.

## Security decisions and known risk

Port `5001` is DSM's shared HTTPS listener, so the tunnel exposes the DSM login surface as well as Drive sharing. This was explicitly accepted after confirming that Drive's reserved package ports were not listening and its web application is served through DSM. Exposure is constrained by the two source-specific firewall rules and the outbound-only tunnel, but it is broader than a Drive-only origin.

Recommended follow-up for Claude:

1. Evaluate Cloudflare Access for the DSM login surface without breaking anonymous Drive public links. A path-aware design may be required; do not apply a blanket Access policy to the hostname without testing share URLs.
2. Consider a dedicated Synology reverse-proxy/application portal rule if DSM can provide a Drive-only origin while preserving generated share links.
3. Add rate limiting or other Cloudflare controls for the DSM login path.
4. Confirm connector and firewall persistence after the next LXC, OPNsense and NAS restart.
5. Decide when to revoke the `HDR Window.jpeg` public test link.
6. Continue the remaining milestones in `docs/projects/Synology-Drive-Family-Cloud.md`.

## Operations

Health checks:

- Cloudflare dashboard: tunnel `synology-drive-share` should be Healthy.
- LXC 107: container `cloudflared` should be running.
- From LXC 107: NAS TCP `5001` should connect.
- External: `https://share.elliottrook.com` should return a Cloudflare-served response.

Rollback order:

1. Disable or delete the Cloudflare published route/DNS record.
2. Stop the `cloudflared` container in LXC 107.
3. Remove the OPNsense source-specific TCP 5001 rule and apply.
4. Restore the Synology pre-change firewall export or remove only the `192.168.50.23 -> TCP 5001` rule.
5. Disable Drive sharing-link customization or restore the previous DDNS setting.

Do not remove the unrelated Synology firewall rule or make broad changes to the default-deny profile.
