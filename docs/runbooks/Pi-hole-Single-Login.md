# Pi-hole single login

Deployed 2026-09-26. Use [primary](https://dns1.elliottrook.com/admin/) and
[secondary](https://dns2.elliottrook.com/admin/) through the existing Authentik
passkey-only owner flow. Both were observed in Brave using an existing Authentik
session without a second application login. Fresh passkey and logout acceptance
remain open; this is not full project graduation.

## Access paths

| Component | Primary | Secondary |
| --- | --- | --- |
| Authority | `/opt/pihole/compose.yaml`, LXC 100 | TrueNAS managed app `pihole` |
| Image unchanged | `pihole/pihole:2026.05.0` | `pihole/pihole:2026.07.2` |
| Browser guard | `192.168.20.20:8082` | `192.168.20.40:20720` |
| Private backend | Host loopback `127.0.0.1:18082` to container 80 | Unpublished `172.31.250.2:20720` |
| FTL web ACL | `+127.0.0.1,+172.19.0.1` | `+127.0.0.1,+172.31.250.1` |
| Guard config | `/opt/pihole/authentik-ingress/nginx.conf` | `/mnt/Media/appdata/authentik-browser-ingress/pihole-secondary/nginx.conf` |
| Guard lifecycle | Service `authentik-pihole-ingress` in primary Compose | `compose.json` alongside secondary guard config |

Both guards require actual NPM source `192.168.50.23` and verified username
`jason`. NPM hosts 16/17 now overwrite `X-Homelab-Authentik-User` from the
Authentik subrequest. Client identity headers cannot satisfy the source check.
Direct IP access returns 403; use the HTTPS links above. State-changing requests
also require the service's exact HTTPS Origin. Foreign Origin and cross-site
fetches are denied. Pi-hole native passwords do not protect the private backend;
never remove the guard, ACL or private binding while retaining this auth mode.
The secondary's native password was already empty before this change.

Guard images remain pinned to nginx digest
`sha256:608a100c71651bf5b773c89083b4a1ad7ef4b2bd05d7a7e552271e03123692ad`,
running UID 101, read-only root, temporary /tmp, no capabilities, no new
privileges, and restart unless-stopped. Reference configurations are tracked as
[primary](../../scripts/authentik/pihole-primary.nginx.conf) and
[secondary](../../scripts/authentik/pihole-secondary.nginx.conf).

## DNS and Docker networks

TCP/UDP 53 remain published exactly as before. DNS data, upstreams, blocklists,
DHCP posture, service images, LAN IPs, firewall rules and split-DNS records were
not changed. The secondary app's supported additional-networks setting replaces
its default Docker network, so it requires **both** of these persistent external
Docker networks:

- `authentik-pihole-private`: internal network `172.31.250.0/29`, gateway `.1`,
  static Pi-hole `.2`. Used only for host guard/recovery access to the web API.
- `authentik-pihole-service`: ordinary bridge `172.31.251.0/29`, gateway `.1`,
  static Pi-hole `.2`, gateway priority 1. Enables normal DNS publication and
  upstream connectivity. Web ACL rejects this network's source addresses.

Both subnets were checked against Docker networks and host routes before use.
They are host-internal service implementation details, not new routed LAN/VLAN
prefixes. Do not delete these networks when stopping the managed app. They are
referenced in its saved TrueNAS network configuration. The app web port uses
`bind_mode: exposed`; it has no host port publication. TrueNAS rejects loopback
host-IP selection, so no unsupported loopback override was used.

During staging, the internal-only network did not support DNS publication.
Validation detected this while the primary continued answering. Adding the
service bridge restored DNS. Subsequent managed stop/start preserved both
networks, static addresses, unpublished HTTP and functional DNS.

## Homepage and other clients

The primary widget uses `http://172.18.0.1:18083`, accepts only
`GET /api/stats/summary` from Homepage `172.18.0.2`, and has no API key in its
widget stanza. The original credential file remains for rollback. Other paths,
methods and peers are denied. Both the isolated and live installed Homepage
widget returned all four numeric statistics.

Homepage's Compose now pins `172.18.0.2` on existing external network
`homepage_default`. Its image is unchanged. Keep that network when managing
Homepage; recreating it with different addressing requires updating this guard
and rechecking denial tests. No other service widget was changed.

Home Assistant has no configured Pi-hole integration or references in its three
main YAML files. Other intermittent clients remain unconfirmed. Add a narrowly
scoped client route if needed; never restore a broad unauthenticated API path.
AI administration remains via authorized host-level operations; there is no
new AI API credential or broker capability in this milestone.

## Recovery

Protected checkpoints:

- NPM: `/opt/nginx-proxy-manager/backups/pihole-single-login-20260926T220448Z`.
- Primary: `/opt/pihole/backups/single-login-20260926T220655Z`; 49 restored files
  compared byte-for-byte, gravity and FTL database integrity OK.
- Secondary: `/root/pihole-single-login-20260926T221046Z`; 133 restored files
  compared by SHA-256, gravity and FTL database integrity OK. Contains original
  managed-app settings and final private/service-network candidate values.
- Homepage source pin: `/opt/homepage/backups/pihole-widget-source-20260926T221149Z`.

Checkpoints contain secrets and DNS history: retain restricted ownership and
permissions, never print them or commit them to Git. Restored copies are retained
as recovery proof. Existing scheduled-backup coverage of the new secondary guard
and host Docker-network definitions still needs a separate close-out check.

For an Authentik/NPM outage, authorized administrators can reach the primary API
from LXC 100 via `127.0.0.1:18082` and the secondary from TrueNAS via
`172.31.250.2:20720`. Both source-local recovery paths were tested. An SSH tunnel
from TrueNAS to the latter address can provide browser recovery without NPM;
interactive tunnel/browser recovery has not yet been accepted by Jason.

Repair guards from the saved Compose/config files. Restore only affected NPM
rows, never the entire shared database over later changes. For primary rollback,
restore its original native authentication configuration **before** restoring its
old LAN port; coordinate the original widget stanza. The secondary's original
state was passwordless: do not restore that exposed HTTP publication. Keep its
backend private while repairing, and retain the primary resolver throughout.

## Verification

All 126 production boundary checks pass, including plain and forged-header
Pi-hole API denial. NPM-source tests allow the verified owner and deny missing,
wrong or foreign-origin requests. TCP and UDP public/private DNS checks pass on
both resolvers. Primary container/guard restart and secondary managed-app
stop/start pass. Unrelated Docker-network access to both secondary addresses is
denied; primary Homepage cannot access the raw backend or configuration API.

Remaining human gates: fresh passkey, logout/session behaviour, settings saves
and upload workflows, and interactive browser recovery. Full host reboot and
scheduled-backup restoration are not claimed by these restart tests.
