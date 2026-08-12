# Operations

SSH shortcuts:
- ssh proxmox
- ssh docker
- ssh opnsense
- ssh truenas
- ssh frigate

## Service dashboard

- LAN and Tailscale URL: `http://home.internal:3000`
- Direct fallback: `http://192.168.1.20:3000`
- Homepage configuration: `/opt/homepage/config` inside Proxmox LXC 100 (`docker`)
- The `SSH Access` group launches the local SSH client for Proxmox, Docker LXC, OPNsense and TrueNAS.
- The `Surveillance` group links to Frigate and launches its SSH connection.

Dashboard SSH targets:

| Tile | Target |
|---|---|
| Proxmox SSH | `ssh://root@192.168.1.10` |
| Docker LXC SSH | `ssh://root@192.168.1.20` |
| OPNsense SSH | `ssh://root@192.168.1.1` |
| TrueNAS SSH | `ssh://truenas_admin@192.168.1.40` |
| Frigate SSH | `ssh://jelliott@192.168.20.10` |

The client device must have an application registered to handle `ssh://` links. These links do not contain passwords or private keys.

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
- TrueNAS export: `192.168.1.40:/mnt/Media/Surveillance/Frigate`
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

- Primary host: Proxmox LXC 100 (`docker`), `192.168.1.20`
- Compose project: `/opt/pihole`
- Persistent configuration: `/opt/pihole/etc-pihole`
- Primary image: `pihole/pihole:2026.05.0`; internal hostname: `pihole-primary`
- Primary endpoints: `192.168.1.20:53` over TCP/UDP and `http://192.168.1.20:8082/admin/`
- Secondary host: TrueNAS App `pihole`, `192.168.1.40`
- Secondary image observed during rollout: `pihole/pihole:2026.07.2`
- Secondary endpoints: `192.168.1.40:53` over TCP/UDP and `http://192.168.1.40:20720/admin/`
- Upstream resolver: OPNsense Unbound at `192.168.1.1`
- Public, blocked-domain and `internal` resolution passed through both instances.
- DHCP remains on OPNsense; Pi-hole DHCP is disabled.
- OPNsense Dnsmasq sends `192.168.1.20,192.168.1.40` as DHCPv4 option 6 on every configured DHCP range.
- `PIHOLE_DNS_SERVERS` contains both resolvers; `PIHOLE_CLIENT_NETWORKS` contains VLANs 20 through 70.
- The floating `Allow client VLANs to Pi-hole DNS` rule permits only TCP/UDP 53 and precedes the existing RFC1918 isolation blocks.

Health and validation:

```sh
# Run in LXC 100
cd /opt/pihole
docker compose ps
docker compose logs --tail 100

# Run from a LAN client
dig +short @192.168.1.20 example.com
dig +short @192.168.1.20 home.internal
dig +short @192.168.1.20 doubleclick.net
dig +short @192.168.1.40 example.com
dig +short @192.168.1.40 home.internal
dig +short @192.168.1.40 doubleclick.net
```

Expected results from either resolver are public addresses for `example.com`, `192.168.1.20` for `home.internal`, and `0.0.0.0` for a blocked `doubleclick.net` query.

Network-wide rollback:

1. Remove or disable the untagged Dnsmasq DHCP option 6 and apply changes. Dnsmasq will resume advertising the receiving OPNsense interface as DNS.
2. Renew a test client's DHCP lease and confirm it receives the OPNsense interface address.
3. Disable the consolidated floating Pi-hole rule only after clients have moved back; the aliases can remain without affecting traffic.

DHCP-provided DNS does not force clients to use port 53. iCloud Private Relay, VPNs and encrypted-DNS profiles may bypass the Pi-hole pair unless a separate, explicitly approved enforcement policy is deployed.

## Remote administration

- Tailscale subnet router: `homelab-gateway` in Proxmox LXC 100
- Advertised route: `192.168.1.0/24` only
- IoT and Guest routes are intentionally not advertised.
- Tailnet split DNS forwards only the `internal` namespace to OPNsense.
- Tailnet policy grants the administrator identity access to the trusted LAN; the broad default allow-all rule is removed.
- Remote OpenSSH access to Proxmox, Docker LXC, OPNsense and TrueNAS was validated over the subnet route with the client off the home Wi-Fi network.
- This is ordinary SSH transported through Tailscale. Native Tailscale SSH is not enabled and is not required for the routed LAN hosts.
- Do not expose OPNsense, Proxmox, TrueNAS, UniFi, Portainer or Homepage directly to the public Internet.
- Do not add an inbound WAN SSH rule or port-forward. A remote client must be authenticated to the tailnet and authorized by the identity-specific grant.
