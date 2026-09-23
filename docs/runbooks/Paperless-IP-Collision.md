# Paperless UI collision — 2026-09-23

Resolved on 2026-09-23: Paperless is now 192.168.70.15; Speech remains .14.
The current Homepage link is https://paperless.elliottrook.com. The following
diagnosis and plan are retained as incident history.

- LXC 115 `paperless-ngx`: 192.168.70.14, MAC BC:24:11:62:1D:25.
- LXC 116 `aster-speech`: 192.168.70.14, MAC BC:24:11:E1:11:68.
- OPNsense ARP maps .14 to the speech guest's MAC. Paperless localhost login is
  HTTP 200; the Mac receives connection refusal on .14:8000.
- NetBox address 30 assigns .14 to aster-speech interface 16. Paperless has no VM
  inventory entry. Do not modify speech's identity or its existing firewall rules.
- Candidate .15 is absent from Proxmox guest configs and NetBox, has no matching
  OPNsense configuration value, gives no ping response and has incomplete ARP.
  Recheck immediately before use; discovery is not a reservation.

## Completed UI work

- Added OPNsense rule fdc0bfb3-9dd4-4bca-869c-a571f8d64f02:
  MGMT_ADMIN_HOSTS -> 192.168.70.14:8000/TCP on LAN, sequence 3151.
  Filter reload succeeded and the rule is present in pf.
- Added Paperless-ngx tile under Application Management; restarted only Homepage.
  Live `/api/services` confirms the tile and URL.
- Firewall rollback copy:
  `/conf/backup/config-paperless-ui-before-20260923-184448.xml`.
- Homepage rollback copy inside container:
  `/app/config/services.yaml.before-paperless-1790189098716`.

## Confirmed correction — completed

Task-specific confirmation is recorded in [AGENTS.md](../../AGENTS.md), dated
2026-09-23. The correction was applied and validated.

Move only LXC 115 to 192.168.70.15/24, preserving its gateway, VLAN, MAC and other
configuration. Exact network setting:

```
name=eth0,bridge=vmbr0,gw=192.168.70.1,hwaddr=BC:24:11:62:1D:25,ip=192.168.70.15/24,tag=70,type=veth
```

Update only the new Paperless firewall rule destination and Paperless tile URL
from .14 to .15. Reload the firewall and restart only Homepage as needed.
Register Paperless and .15 in NetBox to prevent recurrence; do not repoint the
existing speech address record. Save configuration checkpoints first.

Validate the login page and static assets from the Mac, check the UI in a browser,
confirm guest health and correct ARP mapping, and confirm unapproved VLAN 20
still cannot reach the application. A short Paperless network interruption is
expected; no application data changes are needed.

If readdressing fails, stop and inspect the guest via `pct exec`; do not restore
an active .14 assignment and recreate the collision. Keep the guest isolated
if required while retaining the captured configuration and both backup copies.

## Completion evidence

Paperless guest MAC is BC:24:11:62:1D:25 and OPNsense ARP resolves .15 to it.
The backend returned 200 from the approved Mac and was denied from VLAN 20.
NetBox created VM/interface/IP 17/17/31 without changing Speech. Homepage was
first corrected to .15 and then upgraded to the private HTTPS route. NPM host
25 and Authentik provider 34 supply the normal authenticated launch path.

Checkpoints: Proxmox /root/paperless-checkpoints/115-before-ip-20260923.conf;
OPNsense /conf/backup/config-paperless-readdress-20260923-190718.xml;
Homepage /app/config/services.yaml.before-paperless-ip-1790190442991.
The additional NPM-to-.15:8000 rule is c12aa6c7-7df9-4162-9498-a7ad61edc219;
its checkpoint is /conf/backup/config-paperless-https-20260923-192027.xml.
Do not replay the original conflicting network configuration.
