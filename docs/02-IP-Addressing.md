# IP Addressing

|Device|IP|
|---|---|
|OPNsense|192.168.1.1|
|Proxmox|192.168.1.10|
|Docker|192.168.1.20|
|UniFi Controller|192.168.1.21|
|UniFi Switch|192.168.1.30|
|UniFi AP|192.168.1.31|
|TrueNAS|192.168.1.40|
|Synology DS920+|192.168.1.41|
|Backup Synology|192.168.1.42|

## Shared service endpoints on Docker LXC 100

| Service | Address | Port | Status |
|---|---|---:|---|
| Homepage | `http://192.168.1.20:3000` | 3000/TCP | Production |
| Portainer | `https://192.168.1.20:9443` | 9443/TCP | Production |
| Pi-hole DNS | `192.168.1.20` | 53/TCP+UDP | Mac Mini pilot |
| Pi-hole Web | `http://192.168.1.20:8082/admin/` | 8082/TCP | Pilot administration |
| Tailscale subnet router | `homelab-gateway` | Tailscale-managed | Production |
