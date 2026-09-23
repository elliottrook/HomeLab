# Paperless document service

> Authority: current-with-exclusions
> Reviewed: 2026-09-23
> Sources: live Proxmox, Paperless, NetBox, OPNsense, Homepage, Authentik and backup verification; Document OCR project close-out.

## Access and ownership

Open https://paperless.elliottrook.com from an approved management device. The
Homepage Application Management tile opens this HTTPS address. Authentik gates
access to Jason; Paperless then uses its native `jason` account. The existing
native bootstrap credential remains protected on LXC 115 at
`/root/.paperless-temp-password`; never copy it into Git, chat or logs. Complete
personal sign-in and credential replacement through the normal operator flow.

The proxy allows management clients 192.168.1.206, 192.168.1.241 and
192.168.1.112 (Jason’s registered iPhone), plus the existing Tailscale subnet
router at 192.168.20.20. The router translates remote clients to that source
address; Authentik still restricts access to Jason. Other sources, including the
public tunnel, are denied. Use the same HTTPS URL on home Wi-Fi and with
Tailscale connected away from home. No Lab-VLAN route was added. Direct
http://192.168.70.15:8000 remains a restricted administrative recovery endpoint.
Native authentication is retained; no anonymous access or trusted-header login
was enabled. Certificate renewal is owned by NPM's existing wildcard certificate.
Both private Pi-hole resolvers map paperless.elliottrook.com to 192.168.50.23.

## Deployment

Paperless-ngx 3.1.3 is on Proxmox LXC 115, Debian 13, 2 vCPU, 2048 MiB RAM and
32 GiB storage. Its address is 192.168.70.15/24 on VLAN 70. Aster Speech LXC 116
owns 192.168.70.14; never restore Paperless to that conflicting address.
NetBox VM/interface/IP IDs are 17/17/31. Docker Compose is in /opt/paperless-ngx,
with protected environment in docker-compose.env. The SQLite database and media
are named Docker volumes. The application server is Granian; nginx is the
separate HTTPS reverse proxy.

## OCR and summaries

Upload documents through Paperless or place files in its consume directory.
Paperless performs OCR. The Document Added workflow grants the dedicated
view-only reader access; the five-minute timer polls visible documents and writes
only the `AI summary` custom field. It processes all documents without a sensitive
category exclusion. No documents or OCR go to an external AI provider.

Inference uses LXC 110 at 192.168.70.12:11435 and a dedicated revocable key.
The unprivileged worker has no Paperless token or Docker access. A local Unix
broker exposes only page/read/publish; the token remains in Paperless's database.
The writer has no password or token and gates the one-field capability. Central
AI-PAM custody remains an integration follow-up; source-local custody is used.

A complete scan reconciles removed or inaccessible documents. Changes invalidate
old summaries. Inference failures never publish partial summaries. One due
document is processed per cycle; long text is processed in bounded sections up
to 96,000 characters. Larger or empty OCR is reported as unavailable and retried.
The timer waits five minutes after a cycle completes; a long document can take
several minutes. Summaries are derived aids, not an authority for decisions.

## Health, backup and recovery

On LXC 115, `python3 /opt/paperless-summary/check_summary.py` checks the UI,
broker, timer, worker health and freshness. The HomeLab Doctor hook is installed in the operational checkout and its
focused check passed. It uses the existing failure-report channel. Worker status lives under
/var/lib/paperless-summary/status.json; logs omit document bodies and credentials.

Local Proxmox and TrueNAS whole-guest backups retain database, originals,
credentials and derived state. Offsite backup is service-only: an exact allowlist
of software, pinned deployment templates and non-secret configuration. It excludes
database, originals, OCR, summaries, credentials and runtime state. Seven old
offsite whole-guest archive versions were removed on 2026-09-23; future LXC 115
archives are excluded from the relay. Service releases are exported after changes;
the existing daily relay maintains the accepted service export offsite.

Stop the summary timer and broker to disable summaries without stopping Paperless.
Deactivate the dedicated reader/writer to revoke integration access. Restore
whole-guest data only from the local/TrueNAS backup, first into an isolated guest
with no NIC. Recheck address ownership before reconnecting a recovered instance.
See the Paperless summary operations and isolated restore runbooks in HomeLab.

## Uncertain or excluded

The deployment tests use labelled synthetic documents; there was no real corpus.
Jason must check initial real-document quality and personally complete the
browser login. No claim is made that Codex completed a personal MFA ceremony.
Native recovery access is restricted HTTP, not the normal launch route. Inputs
over 96,000 characters require manual handling or a future capacity change.
