# Operations

SSH shortcuts:
- ssh proxmox
- ssh docker
- ssh opnsense
- ssh truenas
- ssh frigate
- ssh nut
- ssh root@192.168.20.31

## Authorization

- Nginx Proxy Manager: `https://proxy.elliottrook.com`
- Expected login chain: Authentik password, WebAuthn/passkey, then NPM credentials
- State: tested and working on 2026-08-22
- Direct fallback: `http://192.168.50.23:81` from trusted management networks
- Detailed validation, regeneration and rollback procedure: [Authorization](08-Authorization.md)
- Repeatable process for each additional service: [Service Authorization Onboarding](09-Service-Authorization-Onboarding.md)

## Service dashboard

**2026-09-04/05: evaluated replacing Homepage with Homarr; decided against it.**
Homepage's YAML-only layout couldn't do the tile arrangement wanted (e.g. one
tall tile beside two stacked ones), which prompted a full trial migration to
Homarr. The migration itself hit real friction — Homarr's "add app"/"new
item" board-editor modal reliably rendered empty (zero height) in the
automation browser used to drive the session, blocking further scripted
setup — and Jason ultimately preferred Homepage's structure for the main
ops dashboard. **Homepage remains the primary dashboard**; nothing about it
changed as a result of the trial. Homarr is being **kept as a secondary,
purpose-specific board** for media app management (a `Media Manager` tile
was added under Homepage's `Media Automation` group linking to it), which
Jason is customizing by hand.

- Homarr URL: `http://192.168.20.20:7575`
- Homarr config/data: `/opt/homarr/appdata` (bind-mounted), compose file at
  `/opt/homarr/compose.yaml`, secrets (admin password, Beszel read-only
  account password, Jellyfin/Immich/Seerr API keys) at `/opt/homarr/secrets/*`
  (mode 600, outside Git)
- Admin login: username `jelliott`; password in `/opt/homarr/secrets/admin_password`
  — change it via Homarr's own account settings once logged in
- Docker socket is deliberately **not** mounted into the Homarr container —
  container stats go through Portainer's API instead, keeping the same
  least-privilege posture used throughout this project rather than granting
  Homarr root-equivalent host access
- Integrations configured: Sonarr, Radarr, Prowlarr, Lidarr, SABnzbd, Beszel,
  TrueNAS, Proxmox, Pi-hole Primary, Jellyfin, Immich, Seerr. Audiobookshelf
  and Calibre intentionally left for Jason to set up himself — the "Calibre"
  tile turned out to be the actual desktop Calibre app streamed via Selkies
  remote-desktop (not calibre-web), so it has no REST API and can never get a
  widget; Audiobookshelf just wasn't gotten to.
- Beszel required a new dedicated `readonly`-role account
  (`homarr-widget@home.internal`) rather than reusing Homepage's existing
  superuser account — Homarr's integration uses Beszel's regular hub login
  (the `users` PocketBase collection), which the superuser account (a
  `_superusers` record, a separate auth system) can't authenticate against.
  Beszel also scopes system visibility per-user via a `users` relation field
  on each `systems` record — the new account saw zero systems until it was
  added to that field on all 7. Both were net privilege reductions, not just
  workarounds.
- Found and fixed a live bug while wiring up TrueNAS: its own security policy
  auto-revokes any API key the moment it's used over plain HTTP ("Attempt to
  use over an insecure transport"). Homepage's TrueNAS widget was doing
  exactly that; its key had been silently revoked. Rotated the key and moved
  Homepage's TrueNAS widget to `https://` to fix it going forward, then
  repeated the same fix in Homarr, trusting Proxmox's PVE cluster CA
  certificate (`/etc/pve/pve-root-ca.pem`, uploaded to Homarr) and TrueNAS's
  self-signed cert along the way.
- OPNsense integration deliberately not attempted in either dashboard — no
  safe CLI-native way to mint a credential, and it's the gateway.

- LAN and Tailscale URL: `http://home.internal:3000`
- Direct fallback: `http://192.168.20.20:3000`
- Homepage configuration: `/opt/homepage/config` inside Proxmox LXC 100 (`docker`)
- The `SSH Access` group launches the local SSH client for Proxmox, Docker LXC, OPNsense and TrueNAS.
- `Security & Operations` groups Beszel, Code Server, Authentik, Dockge, Dozzle and Nginx Proxy Manager.
- `AI & Automation` identifies the isolated Hermes and Ollama pilots without publishing inaccessible direct links.
- `Application Management` contains File Browser and Forgejo.
- `Security & Surveillance` links to Frigate and launches its SSH connection.

Most service tiles now carry live Homepage widgets (system/queue stats pulled
from each app's own API) rather than static links — see the 2026-09-02
activity log entry below for the full list and the credential pattern used.
Proxmox and TrueNAS widgets are live, each backed by a dedicated
least-privilege read-only credential (a privilege-separated API token with the
built-in `PVEAuditor` role for Proxmox; a dedicated API key on the
`truenas_admin` account for TrueNAS). The OPNsense widget remains
intentionally deferred — it has no safe CLI-native way to mint an API key
(unlike Proxmox/TrueNAS), so wiring it up needs a short GUI step on the
firewall itself with Jason present. API secrets are never placed directly in
the tracked Homepage YAML; they're written to `/opt/homepage/secrets/*` files
(mode 600, outside Git) and referenced from `services.yaml` via
`{{HOMEPAGE_FILE_*}}`, the same pattern already used for Beszel.

**2026-09-05: group render order and within-group gap fixes.** Two things
learned while tidying the layout further: (1) group **display order** is
driven by the key order in `settings.yaml`'s `layout:` map, not by
`services.yaml`'s document order — reordering groups in `services.yaml`
alone has no visible effect. (2) within a `style: row` group, the row height
matches its tallest cell, so pairing a widget tile (tall) with a plain-link
tile (short) in the same row leaves visible dead space under the short one.
Fixed by reordering items within each affected group so widget tiles either
pair with other widget tiles or land alone (odd-one-out, empty cell beside
them, no stretch): `Network` (Pi-hole Primary moved last), `Security &
Operations` (Beszel moved last), `Storage` (Synology A/B paired, TrueNAS
last; also dropped from 3 to 2 columns to make the pairing work). `Newtarr`
moved from `Media Automation` to `Application Management` since it was the
only static tile among five widget tiles there and had nowhere clean to
land — `Application Management` is all static links, so it fits without
a gap. `Security & Surveillance` moved up in `settings.yaml`'s layout order
to sit directly under `Smart Home`, per Jason's request. One known residual
gap: the `Media Manager` tile (added to `Media Automation`) is a static tile
among five widget tiles with no odd-one-out slot available (even count) —
left as-is since moving it would mean dropping it from Media Automation,
which was the point of adding it there.

Dashboard SSH targets:

| Tile | Target |
|---|---|
| Proxmox SSH | `ssh://root@192.168.50.10` |
| Docker LXC SSH | `ssh://root@192.168.20.20` |
| OPNsense SSH | `ssh://root@192.168.1.1` |
| TrueNAS SSH | `ssh://truenas_admin@192.168.20.40` |
| Frigate SSH | `ssh://jelliott@192.168.20.10` |

The client device must have an application registered to handle `ssh://` links. These links do not contain passwords or private keys.

TrueNAS intentionally has two working administrative SSH accounts:
`truenas_admin` (used by the dashboard tile above; also the identity used by
the Plex-to-Jellyfin migration tooling, member of the `apps` group) and
`root` (used by the Mac's `ssh truenas` alias). Both are members of
`builtin_administrators`. Confirmed 2026-09-01: both currently authenticate
with the same SSH key, so in practice one key grants root-equivalent access
under either username — an accepted, understood tradeoff, not a
documentation error.

## Prometheus observability pilot

- Guest: unprivileged Proxmox LXC 109 (`observability`)
- Address: `192.168.20.31` on Servers VLAN 20
- Prometheus: `http://192.168.20.31:9090` from approved private networks only
- Grafana: `https://monitoring.elliottrook.com` through the private reverse
  proxy; `http://192.168.20.31:3000` remains the private recovery path
- Version/limits: Prometheus 3.13.2 LTS, 90-day and 20 GB TSDB ceilings
- Grafana version/limits: Grafana OSS 13.2.0, 1 CPU and 768 MB service ceiling
- Services: `prometheus`, `grafana-server`, `pve-exporter`, `nut-exporter`,
  `graphite-exporter` and `truenas-graphite-ingress`
- Configuration: `/etc/prometheus`; `pve.yml` contains the read-only API token
  and must remain mode-protected and outside Git
- Grafana configuration: `/etc/grafana`; dashboards are provisioned from
  `/var/lib/grafana/dashboards`. The initial administrator recovery credential
  is in the protected backup and `/root/.grafana-initial-admin-password` on the
  guest; never copy it into Git or routine documentation.
- Grafana Authentik OIDC is restricted to the Authentik administrators group.
  Its client secret is stored in the protected `/etc/grafana/oauth.env` and is
  included only in protected backups. Local login and the direct address remain
  available for recovery.
- Grafana evaluates only two provisioned UPS rules: on-battery for 30 seconds,
  and low/replace-battery or charge at the device threshold for two minutes.
  Email to `jason@yampy.ca` is the selected notification path and its contact
  point is provisioned. Grafana authenticates to iCloud SMTP on TCP 587 with
  mandatory STARTTLS using the protected `/etc/grafana/smtp-icloud.env` file.
  A controlled Grafana-generated test was received successfully; the temporary
  rule was then removed and only the two production UPS rules remain.
- Provisioned HomeLab dashboards: Infrastructure Overview, Compute Storage and
  Network, Frigate Surveillance and AI, and Power Resilience. The focused
  backup archive is the current configuration-level recovery point.

Routine validation:

```sh
ssh root@192.168.20.31 "systemctl is-active prometheus grafana-server pve-exporter nut-exporter graphite-exporter truenas-graphite-ingress"
ssh root@192.168.20.31 "promtool check config /etc/prometheus/prometheus.yml"
curl -fsS http://192.168.20.31:9090/-/ready
curl -fsS http://192.168.20.31:3000/api/health
curl -fsS http://192.168.20.31:9090/api/v1/targets
```

All exporters are observational only. Do not restart a monitored service to
repair a failed scrape. Diagnose the exporter, its narrow network path and its
read-only identity instead.

## UPS / power monitoring

Quick reference for checking UPS status without opening a browser:

```sh
ssh nut "upsc -l"                              # list all three UPS units
ssh nut "upsc proxmox-ups@localhost"           # full status for one unit
ssh nut "upsc nas-ups@localhost ups.status"    # single field
ssh nut "upsc network-ups@localhost ups.status"
```

`ups.status` of `OL` means on mains and healthy; `OB` means on battery;
`LB` means the unit has crossed its configured low-battery threshold
(`nas-ups`=50%, `proxmox-ups`=80%, `network-ups`=25% — not the hardware
default). HomeLab Doctor's `check_nut` and `check_backup_age "NUT"`
cover the same ground automatically, and Beszel shows the Lenovo's own
host-level metrics (not UPS-specific data) in its dashboard.

Full architecture, shutdown behavior and recovery notes:
[UPS-Power-Resilience-Claude-Handover.md](UPS-Power-Resilience-Claude-Handover.md).

## Activity log — 2026-09-02

Upgraded the Homepage dashboard from static links to live widgets on every
tile where Homepage has a supported integration, and repaired a real *arr
stack outage caused mid-project by an API key rotation.

- Rotated the Sonarr/Radarr/Prowlarr/Lidarr/SABnzbd API keys after one was
  accidentally echoed into a terminal transcript, then discovered a second,
  unrelated bug while chasing down a stale-value mismatch: `/mnt/Media/configs/<app>/`
  on TrueNAS is a leftover, disconnected directory for each of these apps —
  their real config (and live API key) lives in TrueNAS's managed
  `/mnt/.ix-apps/docker/volumes/<uuid>/_data/` volume instead. Reading the
  stale path after rotating produced confidently-wrong key values.
- That mismatch, plus the key rotations themselves, broke live functionality:
  Prowlarr's "Apps" integration stores Sonarr/Radarr's API key to push
  indexer configs to them, and each synced indexer entry embeds Prowlarr's
  *own* key too — so rotating Prowlarr's key cascaded into "all indexers
  unavailable" health failures on both Sonarr and Radarr, on top of the
  direct Prowlarr→Sonarr/Radarr connection breaking. Fixed by correcting the
  stored keys in Prowlarr's Apps settings and forcing an immediate
  "Sync App Indexers"; all three confirmed healthy afterward
  (`No issues with your configuration`).
- Added Homepage widgets, each backed by a dedicated credential stored under
  `/opt/homepage/secrets/` (mode 600, outside Git) and referenced from
  `services.yaml` via `{{HOMEPAGE_FILE_*}}` — the existing Beszel pattern:
  Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd (API keys), TrueNAS (dedicated
  API key on `truenas_admin`), and Proxmox (privilege-separated API token,
  `PVEAuditor` role only, at path `/`).
- Enabled authentication on Lidarr (Forms, disabled for local addresses,
  matching Sonarr/Radarr/Prowlarr's existing pattern) — it previously had
  none configured, which was a pre-existing gap unrelated to this change but
  blocked wiring up its widget until addressed.
- Left several recommended widgets **not done** this session — no safe,
  unattended way to obtain credentials for them: OPNsense (no CLI-native API
  key path, and it's the gateway/firewall — too high blast-radius to
  hand-edit unsupervised); Pi-hole ×2, UniFi, Grafana, Portainer, Nginx Proxy
  Manager, Authentik, Tailscale, Jellyfin, Plex, Immich, Seerr,
  Audiobookshelf, File Browser, Forgejo — each needs an admin-panel login
  Claude didn't have standing credentials for, and the session's automatic
  guardrails correctly declined to push through those logins unattended.
  Calibre also needs a quick check first (Homepage's widget targets
  calibre-web specifically, not the stock Calibre content server — unclear
  which this tile actually runs). Revisit with Jason present.

## Activity log — 2026-08-22

The Homepage operations dashboard and its editing workflow were reviewed and validated.

- Deployed and validated code-server in Docker LXC 100 as the HomeLab configuration editor.
- Mounted `/opt/homepage` directly into the code-server workspace so the live Homepage files remain the source of truth, then corrected ownership so code-server can save the YAML configuration.
- Added Code Server and Authentik tiles to Homepage.
- Corrected internal service links that stalled over HTTPS, retained HTTPS where intentional and corrected a changed NAS application port.
- Verified the dashboard groups and links across the current HomeLab service inventory.

The dashboard now acts as an operational overview of the current HomeLab service layer.

![Homepage dashboard on 2026-08-22](homepage-dashboard-2026-08-22.png)

## Network incident — 2026-08-23

A storm caused a site power interruption. The UniFi PoE switch did not return to service when power was restored, repeating its previous failure-to-boot behaviour.

- Standard power-cycle and recovery attempts did not restore the UniFi switch.
- A TP-Link TL-SG1016PE V2 was connected as a temporary PoE fallback, with its uplink on port 16, access points on ports 1 and 3, and the Reolink camera initially on port 2.
- Arista Et33 remained connected and unchanged. It continued to learn downstream access-point and client MAC addresses and showed tagged traffic on VLANs 30, 40 and 50.
- Because the TP-Link was not configured for VLANs, the camera appeared temporarily on Trusted VLAN 10 instead of Cameras VLAN 60. The camera was disconnected while switch management was investigated.
- The TP-Link continued forwarding Ethernet and supplying PoE, but neither its web-management interface nor the Easy Smart discovery utility responded. Direct connection, alternate cables and ports, and a factory reset did not restore management access. The TP-Link was rejected as a manageable replacement.
- After approximately one hour, the UniFi switch started without further intervention. The access points and other attached services reconnected.

Service was restored, but the delayed recovery confirms that the UniFi PoE switch is not reliable after a power interruption. Return or replace it with a stable managed PoE switch that supports the existing native VLAN 10 and tagged VLANs 30, 40, 50 and 60. Before closing the incident, confirm that the Reolink camera is again on `192.168.60.10` and that Frigate recording has resumed.

The Mac SSH client uses the same `~/.ssh/id_ed25519` identity for the documented aliases. OPNsense and Frigate accept its public key, while the private key remains on the Mac. `AddKeysToAgent yes` and `UseKeychain yes` allow macOS to retrieve the passphrase from Apple Keychain and load the identity into `ssh-agent`; FileVault and automatic screen locking remain important because an unlocked user session can use the loaded key.

Validated commands:

```sh
ssh -o BatchMode=yes opnsense 'echo OPNsense-SSH-KEY-OK'
ssh -o BatchMode=yes frigate 'echo Frigate-SSH-KEY-OK'
lab ssh frigate
```

## Frigate operations

- VM: Proxmox VM 102, Debian 13.6, `192.168.20.10` on VLAN 20
- Compose project: `/opt/frigate`
- Web interface: `https://192.168.20.10:8971`
- Configuration: `/opt/frigate/config`
- Recording mount: `/opt/frigate/storage`
- TrueNAS export: `192.168.20.40:/mnt/Media/Surveillance/Frigate`
- Startup unit: `frigate-compose.service`

Health check:

```sh
findmnt -rn -t nfs4 -T /opt/frigate/storage
systemctl is-active frigate-compose.service
cd /opt/frigate
sudo docker compose ps
sudo find /opt/frigate/storage/recordings -type f -mmin -3 | head
```

The systemd service waits until the real NFSv4 mount is available before
starting Compose. Docker's container restart policy is disabled for this stack;
systemd owns startup and recovery so Docker cannot race the NFS mount during
boot. Do not replace the mount with the local directory if TrueNAS is
unavailable.

The dated Frigate configuration archive contains camera credentials and must
remain outside Git with mode `0600`. Recordings are not included in the
configuration archive because they remain on the TrueNAS surveillance dataset.

## Redundant Pi-hole DNS

- Primary host: Proxmox LXC 100 (`docker`), `192.168.20.20` on Servers VLAN 20
- Compose project: `/opt/pihole`
- Persistent configuration: `/opt/pihole/etc-pihole`
- Primary image: `pihole/pihole:2026.05.0`; internal hostname: `pihole-primary`
- Primary endpoints: `192.168.20.20:53` over TCP/UDP and `http://192.168.20.20:8082/admin/`
- Secondary host: TrueNAS App `pihole`, `192.168.20.40`
- Secondary image observed during rollout: `pihole/pihole:2026.07.2`
- Secondary endpoints: `192.168.20.40:53` over TCP/UDP and `http://192.168.20.40:20720/admin/`
- Upstream resolver: OPNsense Unbound at `192.168.1.1`
- Public, blocked-domain and `internal` resolution passed through both instances.
- DHCP remains on OPNsense; Pi-hole DHCP is disabled.
- OPNsense Dnsmasq sends `192.168.20.20,192.168.20.40` as DHCPv4 option 6 on every configured DHCP range.
- `PIHOLE_DNS_SERVERS` contains both resolvers; `PIHOLE_CLIENT_NETWORKS` contains VLANs 20 through 70.
- The floating `Allow client VLANs to Pi-hole DNS` rule permits only TCP/UDP 53 and precedes the existing RFC1918 isolation blocks.

Health and validation:

```sh
# Run in LXC 100
cd /opt/pihole
docker compose ps
docker compose logs --tail 100

# Run from a LAN client
dig +short @192.168.20.20 example.com
dig +short @192.168.20.20 home.internal
dig +short @192.168.20.20 doubleclick.net
dig +short @192.168.20.40 example.com
dig +short @192.168.20.40 home.internal
dig +short @192.168.20.40 doubleclick.net
```

Expected results from either resolver are public addresses for `example.com`, `192.168.20.20` for `home.internal`, and `0.0.0.0` for a blocked `doubleclick.net` query.

Network-wide rollback:

1. Remove or disable the untagged Dnsmasq DHCP option 6 and apply changes. Dnsmasq will resume advertising the receiving OPNsense interface as DNS.
2. Renew a test client's DHCP lease and confirm it receives the OPNsense interface address.
3. Disable the consolidated floating Pi-hole rule only after clients have moved back; the aliases can remain without affecting traffic.

DHCP-provided DNS does not force clients to use port 53. iCloud Private Relay, VPNs and encrypted-DNS profiles may bypass the Pi-hole pair unless a separate, explicitly approved enforcement policy is deployed.

## Home Assistant pilot

- Platform: Home Assistant OS 18.2 in Proxmox VM 103
- Address: `192.168.20.11` on Servers VLAN 20
- Local URL: `http://home-assistant.home.internal` (TCP 80 in the current HAOS deployment)
- Resources: 2 vCPU, 4 GB RAM, 32 GB SCSI disk
- Proxmox settings: OVMF, Q35, VirtIO NIC tagged VLAN 20, automatic startup enabled
- DHCP/DNS: Dnsmasq host reservation for MAC `BC:24:11:08:16:A3`; domain `home.internal`
- Initial recovery point: full Home Assistant backup `Fresh HAOS installation`
- First integration: Philips Hue bridge `192.168.30.164`
- IoT firewall access: TCP/UDP from Home Assistant host `192.168.20.11` to IoT VLAN 30, above the general Servers RFC1918 block
- Lutron Caséta bridge: reserved `192.168.30.102`; devices imported and control validated
- Hue bridge: reserved `192.168.30.164`; devices imported
- Aqara M3: reserved `192.168.30.158`; Matter integration contains six live water sensors, the shutoff valve and lock
- Community integration manager: HACS is installed and authenticated. Add community repositories only when they satisfy an approved integration requirement; installation alone is not approval to expand scope.
- Laundry automation pattern: Hue Hall motion calls the `Laundry motion lighting` script; the script activates the `Laundry bright` scene and starts the five-minute `Laundry occupancy timer`; a separate `timer.finished` automation turns off `Laundry Main Lights`. Use traces to validate each stage.
- Discovery: mDNS repeater limited to LAN, Servers and IoT
- Pilot automation: Hue `Hall Sensor` motion turns on Lutron `Laundry Main Lights`; validated 2026-08-13
- Household access: local non-administrator account validated for dashboard and device control
- Apple presentation: HomeKit Bridge paired with the existing Apple Home; ordinary Siri control is validated while Home Assistant remains the sole device-management and automation authority
- HomeKit domains: `light`, `switch`, `lock`, `climate`, `cover`, `fan`, `vacuum`, `scene`, `script` and `binary_sensor`
- HomeKit exclusions: media players, cameras, general sensors, automations, buttons and helpers to prevent duplication and clutter

Selected Apple/media endpoints and Sonos control are validated. The
Trusted-media alias and ordered Home Assistant rule remain active. Add any
remaining fringe-vendor endpoint only when a planned use case justifies it;
vendor applications remain responsible for firmware, recovery and unsupported
features.

HomeKit Bridge depends on mDNS discovery and client reachability to VM 103. The
existing mDNS repeater is limited to LAN, Servers and IoT, and the bridge uses
its HomeKit TCP listener (default `21063`). Do not add a broad IoT-to-Servers
rule. If a specific Apple home hub cannot control the bridge, validate its
source address and the effective firewall rule before adding the smallest
host-scoped exception.

To roll back HomeKit presentation, remove `HomeBridge` from Apple Home and then
remove or disable the HomeKit Bridge integration in Home Assistant. This does
not remove the underlying Home Assistant integrations, entities, scripts,
scenes or automations. Native Home Assistant and VM-level backups preserve the
hidden HomeKit pairing state needed for recovery.

The Hue bridge registration button must be pressed and released immediately
before submitting the pairing prompt. Automatic discovery is used only where
the explicitly bounded LAN/Servers/IoT mDNS repeater is required; known hub
addresses remain preferred where supported.

Frigate cameras, images and detection sensors can be integrated later, but the
full integration requires a shared MQTT broker, MQTT configuration in both
Frigate and Home Assistant, and the Frigate integration. Treat that as a bounded
follow-up after the first cross-ecosystem automation succeeds.

## Remote administration

- Tailscale subnet router: `homelab-gateway` in Proxmox LXC 100
- Advertised routes: `192.168.1.0/24` and `192.168.20.0/24`
- IoT and Guest routes are intentionally not advertised.
- Tailnet split DNS forwards only the `internal` namespace to OPNsense.
- Tailnet policy grants the administrator identity access to the Trusted and Servers networks; the broad default allow-all rule is removed.
- Remote Homepage, Home Assistant, Frigate and Proxmox access was validated after the Docker/Tailscale gateway moved to Servers VLAN 20, with the client off the home Wi-Fi network.
- This is ordinary SSH transported through Tailscale. Native Tailscale SSH is not enabled and is not required for the routed LAN hosts.
- Do not expose OPNsense, Proxmox, TrueNAS, UniFi, Portainer or Homepage directly to the public Internet.
- Do not add an inbound WAN SSH rule or port-forward. A remote client must be authenticated to the tailnet and authorized by the identity-specific grant.

## Configuration drift detection

The drift detector compares the newest protected OPNsense, Arista and Proxmox backups with an explicitly accepted known-good baseline. The monitoring state contains hashes and configuration paths rather than configuration values or credentials.

Run `lab drift` to check, `lab drift status` to inspect the baseline, and `lab drift accept` only after reviewing an intentional change and confirming that HomeLab Doctor is healthy.

Drift never replaces the baseline automatically. Repeated checks continue to show unresolved drift while suppressing duplicate email for the same condition.

State is stored outside Git under `~/lab/monitoring-state/drift/`.

### Baseline acceptance record — 2026-09-04

Baseline moved from the 2026-08-29 exports to the 2026-09-02 exports (70
protected entries) after auditing all twelve reported differences against the
work that produced them. Every change was additive and attributable; **nothing
was removed, broadened or weakened anywhere**. Recorded here so the next drift
alert has a reference point for what the baseline already contains.

| Drift entry | Actual change | Attributed to |
|---|---|---|
| `arista:running-config` / `startup-config` | `Et17` description `TrueNAS-Failover-Servers` → `Family-Room-AppleTV`, access VLAN 20 → 10 | Apple TV VLAN move, 2026-09-02 (`NetBox-DCIM.md`) — present in *both* running and startup config, so it was saved |
| `proxmox:lxc/109.conf` (added) | New guest | Prometheus/Grafana observability project |
| `proxmox:lxc/110.conf` (added) | New guest | Aster llama.cpp GPU inference |
| `proxmox:lxc/111.conf` (added) | New guest | NetBox DCIM project |
| `proxmox:lxc/104.conf` | Added snapshot `aster-production-20260831` | Aster production rollback checkpoint |
| `proxmox:qemu-server/105.conf` | Added `hostpci0` GPU passthrough + snapshot `pre-b60-passthrough` | Intel Arc Pro B60 passthrough work |
| `proxmox:etc/pve/user.cfg` | Added `prometheus@pve` user, tokens `prometheus@pve!observability` and `root@pam!homepage`, ACL granting both **PVEAuditor** (read-only) | Observability scraping and the Homepage Proxmox widget |
| `opnsense:OPNsense/Firewall` | **+8 rules, −0.** All host-specific single source → single destination:port | See below |
| `opnsense:OPNsense/unboundplus` | +2 DNS host overrides: `git.elliottrook.com` and `monitoring.elliottrook.com`, both → NPM at `192.168.50.23` | Forgejo and Grafana private HTTPS access |
| `opnsense:OPNsense` / `opnsense:configuration` | Wrapper hashes covering the above | Consequence of the two entries above |

The eight added firewall rules, all narrowly scoped:

- TrueNAS → Proxmox `:22` and TrueNAS → Mac `:22` — read-only rsync backup pulls
- Observability → Proxmox `:8006` and → NUT `:3493` — metric collection
- NPM → Forgejo `:3000` and Forgejo → NPM `:443` — Forgejo proxying and Authentik OIDC discovery
- NPM → Grafana `:3000` and Grafana → NPM `:443` — Grafana proxying and Authentik OIDC

The current OPNsense config revision is self-describing (`Add narrow Grafana
proxy and Authentik firewall rules`), which made attribution straightforward.

**Method, for repeating this audit:** `baseline.info` names the exact source
files it was built from, and `~/lab/private-backups/` retains dated copies, so
the honest check is to diff the current export against the named baseline
export rather than inferring intent from the drift entry names. Proxmox host
config is a tarball and must be extracted first; OPNsense rules live under
`OPNsense/Firewall/Filter/rules` in the plugin schema, not the legacy
`filter/rule` node — the latter holds only two rules and will mislead you.

## Scheduled Health Reporting

The `lab report` command runs configuration-drift detection and HomeLab Doctor as one health report.

The macOS LaunchAgent `ca.yampy.homelab-report` runs this report daily at 08:15. Healthy and warning-only results do not generate email. New failures generate an email through `scripts/backup-alert`; unchanged failures are suppressed to prevent duplicate notifications.

The latest combined report and LaunchAgent logs are stored under `~/lab/monitoring-state/reports`. Configuration drift retains its own alert and acknowledgement state.

## Certificate Monitoring

The `lab certificates` command checks the operational TLS endpoints for Proxmox, Portainer, UniFi, TrueNAS and both Synology systems.

## Media libraries (Jellyfin)

Jellyfin (`192.168.20.40:8096`) is the household media server, running as a
Docker Compose service on TrueNAS. Media is served from a single host bind
mount, `/mnt/Media/data` (container path `/media`), under which each
library has its own top-level directory:

| Jellyfin library | Content | Host path |
|---|---|---|
| Movies | Pre-existing Jellyfin movie library | `/mnt/Media/data/media/movies` |
| Shows | Pre-existing Jellyfin TV library | `/mnt/Media/data/media/tv` |
| Music | Canonical, consolidated music library (existing + migrated Plex music) | `/mnt/Media/data/media/music` |
| Archive Movies | Former Plex movie library | `/mnt/Media/data/archive-movies` |
| Archive TV | Former Plex television library | `/mnt/Media/data/archive-tv` |

Archive Movies and Archive TV hold the full former Plex movie/TV
collection, migrated and checksum-verified separately from the pre-existing
Movies/Shows libraries (which remain physically and logically untouched).
The Music library is the single canonical root for all music, combining
what already existed in Jellyfin with the migrated and re-tagged Plex
collection. Full migration history, verification evidence and known
open issues (e.g. a small number of albums that display as multiple
entries due to a Jellyfin metadata-grouping bug) are in
[docs/projects/completed projects/Plex-to-Jellyfin-Media-Migration.md](<projects/completed projects/Plex-to-Jellyfin-Media-Migration.md>).

Jellyfin's own application database (playlists, collections, users, watch
state, plugin configuration) lives separately from the media payload, in a
Docker-managed named volume under `Media/ix-apps` on TrueNAS. See the
"Jellyfin" section of [05-Backups.md](05-Backups.md) for its current
(incomplete) backup coverage.

### Music must be foldered by album, not just tagged (2026-09-06)

**Jellyfin creates a music album entry from the folder, not from tags.**
Tracks sitting loose directly in an artist folder are ingested as
individual tracks but get **no album container** (`AlbumId: null`) — they
effectively vanish from the album view even though their `ALBUM` tags are
perfectly correct. The required layout is:

```text
music/Artist Name/Album Title (Year)/track.flac
```

Symptom to recognise: the Jellyfin dashboard's album count doesn't move
after adding music, and an artist shows only the one or two albums that
happen to live in real subfolders. Note the dashboard's album/song totals
are a **cached figure** and lag reality — query the API for live counts
(`/Items?ParentId=<musicLibraryId>&Recursive=true&IncludeItemTypes=Audio`)
rather than trusting the dashboard when diagnosing.

**Root cause of the 2026-09-06 occurrence — Lidarr's `Rename Tracks` was
disabled.** Lidarr's track format carries the album folder in its *first
path segment*
(`{Album Title} ({Release Year})/{Artist Name} - {Album Title} - ...`), so
with renaming off Lidarr never applies the format at all: imports keep
their original download filenames and land flat in the artist folder.
This had silently orphaned **271 tracks** across Paul Simon (140), Alicia
Keys (119) and The Beautiful South (12). Fixed by moving each file into a
subfolder derived from its own `ALBUM` tag (albums 741 → 757, orphans
271 → 0) and by enabling **Lidarr → Settings → Media Management → Rename
Tracks**, which stops it recurring for future imports.

If music ever "imports but doesn't appear as albums" again, check that
Lidarr setting first — and note that enabling it only governs *future*
imports; existing files need Lidarr's separate bulk rename to be
restructured.

A certificate is considered unhealthy when it cannot be read, its endpoint is unreachable, or it has 30 days or less remaining. Certificate failures are included in the daily failure-only scheduled report and use the existing duplicate-alert suppression.

## Calibre and Audiobookshelf (2026-09-05)

Both apps run as TrueNAS SCALE-managed containers (`ix-calibre-calibre-1`,
`ix-audiobookshelf-audiobookshelf-1`) and were pointed at the household's real
e-book and audiobook libraries, which had been sitting unused on disk:

- E-books: `/mnt/Media/media/books` (851M) — this directory is itself already
  a complete, valid Calibre library (has its own `metadata.db`), not a raw
  file dump. It was mounted into the Calibre container at `/mnt` all along,
  alongside the container's default (near-empty, demo-only) library at
  `/config/Calibre Library`.
- Audiobooks: `/mnt/Media/media/audiobooks` (49GB, ~46 titles, folder-per-book
  with `.m4b` files) — mounted into the Audiobookshelf container at **both**
  `/config` and `/mnt` (a pre-existing double-mount, left as-is since it isn't
  broken and reconfiguring it wasn't in scope).

**Calibre**: no GUI access was available for this change — the container's
UI is a Selkies WebRTC remote desktop that requires an HTTPS-loaded page, and
none of its exposed ports (32014/32015/32016) serve valid TLS reachable from
this environment; this is a standing infra gap, not fixed here. Instead,
Calibre's active-library pointer was changed headlessly: backed up
`/config/.config/calibre/global.py.json`, then edited its `library_path` key
from `/config/Calibre Library` to `/mnt`, then restarted the container so the
running app picked up the change cleanly. Verified via `calibredb list
--library-path=/mnt` before and after restart — 723 real books (Stephen King,
tax guides, etc.), persisted across the restart. The GUI (once the TLS gap is
separately resolved) will now open directly into this real library.

**Audiobookshelf**: the app had never been through first-run setup
(`GET /status` returned `isInit: false` — no admin account, no libraries).
Completed the setup wizard via browser: created a root account named `admin`
(password generated, given to Jason directly in chat — not stored in any repo
or secrets file, since this app has no existing compose/secrets convention
like Homepage or Homarr), confirmed the default Config/Metadata paths
(`/config`, `/metadata`), then added one library ("Audiobooks", media type
Books, folder `/mnt`) and ran a manual scan. Scan completed in well under a
minute, importing all 46 titles with cover art and metadata auto-matched.

Neither app's TrueNAS-side container config, mounts, or the double-mount on
Audiobookshelf were otherwise touched — only each app's own library-path
setting was changed, per the task's scope.
