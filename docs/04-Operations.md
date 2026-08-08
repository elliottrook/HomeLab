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

## Remote administration

- Tailscale subnet router: `homelab-gateway` in Proxmox LXC 100
- Advertised route: `192.168.1.0/24` only
- IoT and Guest routes are intentionally not advertised.
- Tailnet split DNS forwards only the `internal` namespace to OPNsense.
- Tailnet policy grants the administrator identity access to the trusted LAN; the broad default allow-all rule is removed.
- Do not expose OPNsense, Proxmox, TrueNAS, UniFi, Portainer or Homepage directly to the public Internet.
