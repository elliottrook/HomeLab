# Service-only recovery

This export reconstructs software, not the document collection. Paperless 3.1.3
and Valkey images are pinned in paperless-compose.example.yml. LXC 115 is Debian
13, 2 vCPU, 2048 MiB RAM, 32 GiB, unprivileged, nesting/keyctl enabled. The private
address is 192.168.70.15/24, gateway 192.168.70.1, VLAN 70. Check inventory before
assigning an address; never start a duplicate production identity.

Install Docker and Compose, create /opt/paperless-ngx with consume/export
subdirectories, and use the example compose there as docker-compose.yml.
Create a new protected .env and PAPERLESS_SECRET_KEY through the operator's
credential process. Never recover secrets or documents from this export: none
are included. Restore document data only from a separately protected local or
TrueNAS whole-guest archive, preferably using the documented isolated restore.
Recreating an empty service does not recreate its users, database or workflows.

Install summary Python files under /opt/paperless-summary, create the dedicated
paperless-summary system user, and install the supplied systemd units. Use the
repository's scripts/paperless/install_summary_host.sh and provision_integration.py
for a clean deployment, after inspecting for existing integration objects.
Provision the dedicated inference key locally without printing it. Start in
synthetic mode, validate permissions and end-to-end behavior, then promote.

The source repository and operational runbooks describe all approval, firewall,
monitoring and recovery procedures. Database, originals, OCR, summaries, runtime
state and credentials intentionally remain outside this service-only archive.
