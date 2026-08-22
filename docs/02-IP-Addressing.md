# IP Addressing

|Device|IP|
|---|---|
|OPNsense|192.168.1.1|
|Arista Core Switch|192.168.50.2|
|Proxmox|192.168.50.10|
|Docker|192.168.20.20|
|UniFi Controller|192.168.50.21|
|UniFi PoE Switch|192.168.50.30|
|UniFi Hall AP|192.168.50.31|
|UniFi Office AP|192.168.50.141|
|TrueNAS|192.168.20.40|
|Synology DS920+|192.168.20.41|
|Backup Synology|192.168.20.42|
|Frigate VM 102|192.168.20.10|
|Home Assistant OS VM 103|192.168.20.11|
|Hermes Agent LXC 104|192.168.70.10|
|Ollama VM 105|192.168.70.11|
|Reolink Duo 2V PoE|192.168.60.10|

## Shared service endpoints on Docker LXC 100

| Service | Address | Port | Status |
|---|---|---:|---|
| Homepage | `http://192.168.20.20:3000` | 3000/TCP | Production |
| Portainer | `https://192.168.20.20:9443` | 9443/TCP | Production |
| Pi-hole Primary DNS | `192.168.20.20` | 53/TCP+UDP | Production |
| Pi-hole Primary Web | `http://192.168.20.20:8082/admin/` | 8082/TCP | Production administration |
| Tailscale subnet router | `homelab-gateway` | Tailscale-managed | Production |

## Shared service endpoints on TrueNAS

| Service | Address | Port | Status |
|---|---|---:|---|
| Pi-hole Secondary DNS | `192.168.20.40` | 53/TCP+UDP | Production |
| Pi-hole Secondary Web | `http://192.168.20.40:20720/admin/` | 20720/TCP | Production administration |

## Surveillance endpoints

| Service | Address | Port | Status |
|---|---|---:|---|
| Frigate Web | `https://192.168.20.10:8971` | 8971/TCP | Production |
| Frigate SSH | `jelliott@192.168.20.10` | 22/TCP | Administration |
| Reolink HTTP | `192.168.60.10` | 80/TCP | Frigate management |
| Reolink RTSP | `192.168.60.10` | 554/TCP | Video stream |
| Reolink ONVIF | `192.168.60.10` | 8000/TCP | Camera integration |

## Home automation endpoints

| Service | Address | Port | Status |
|---|---|---:|---|
| Home Assistant | `http://home-assistant.home.internal` (`192.168.20.11`) | 80/TCP | Pilot operational |
| Lutron Caséta bridge | `192.168.30.102` | 8081/8083 TCP | Reserved; integrated with Home Assistant |
| Philips Hue bridge | `192.168.30.164` | 80/443 TCP | Reserved; integrated with Home Assistant |

## Local AI Lab endpoints

| Service | Address | Port | Status |
|---|---|---:|---|
| Hermes Agent LXC 104 | `192.168.70.10` | host-dependent | CPU-only pilot |
| Ollama VM 105 API | `http://192.168.70.11:11434/v1` | 11434/TCP | Lab-only pilot |

## Authorization endpoints

| Service | Address | Port | Status |
|---|---|---:|---|
| Nginx Proxy Manager | `https://proxy.elliottrook.com` / `192.168.50.23` | 443/TCP | Tested, Authentik protected |
| NPM direct fallback | `http://192.168.50.23:81` | 81/TCP | Restricted administration |
| Authentik embedded outpost | `http://192.168.50.22:9000` | 9000/TCP | Internal proxy destination |
| Authentik external URL | `https://auth.elliottrook.com` | 443/TCP | Secure browser/WebAuthn origin |
