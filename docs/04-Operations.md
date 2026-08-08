# Operations

SSH shortcuts:
- ssh proxmox
- ssh docker
- ssh opnsense
- ssh truenas

## Service dashboard

- LAN and Tailscale URL: `http://home.internal:3000`
- Direct fallback: `http://192.168.1.20:3000`
- Homepage configuration: `/opt/homepage/config` inside Proxmox LXC 100 (`docker`)

## Pi-hole pilot

- Container host: Proxmox LXC 100 (`docker`), `192.168.1.20`
- Compose project: `/opt/pihole`
- Persistent configuration: `/opt/pihole/etc-pihole`
- Image: `pihole/pihole:2026.05.0`
- DNS listener: `192.168.1.20:53` over TCP and UDP
- Web interface: `http://192.168.1.20:8082/admin/`
- Upstream resolver: OPNsense Unbound at `192.168.1.1`
- Conditional forwarding: `192.168.1.0/24` and the `internal` domain to OPNsense
- DHCP remains on OPNsense; Pi-hole DHCP is disabled.
- Only the Mac Mini Ethernet service is currently configured to use Pi-hole.

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
```

Expected results are public addresses for `example.com`, `192.168.1.20` for `home.internal`, and `0.0.0.0` for a blocked `doubleclick.net` query.

Mac Mini pilot rollback:

```sh
sudo networksetup -setdnsservers "Ethernet" Empty
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

This restores DHCP-provided OPNsense DNS. Do not make Pi-hole network-wide until DNS redundancy and the failure procedure are approved.

## Remote administration

- Tailscale subnet router: `homelab-gateway` in Proxmox LXC 100
- Advertised route: `192.168.1.0/24` only
- IoT and Guest routes are intentionally not advertised.
- Tailnet split DNS forwards only the `internal` namespace to OPNsense.
- Tailnet policy grants the administrator identity access to the trusted LAN; the broad default allow-all rule is removed.
- Do not expose OPNsense, Proxmox, TrueNAS, UniFi, Portainer or Homepage directly to the public Internet.
