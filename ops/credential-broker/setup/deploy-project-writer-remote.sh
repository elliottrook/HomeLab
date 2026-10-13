#!/bin/sh
# Run on the Proxmox host after the credential helper succeeds. The source
# archive is staged by the local operator and contains no credentials.
set -eu

BROKER=104
ARCHIVE=/tmp/homelab-project-writer-source.tar.gz
BASE_REVISION=${1:-}
SOURCE_ROOT=/tmp/homelab-project-writer-source.$$
OLD_BASE=
BASE_CHANGED=0

cleanup() {
    rc=$?
    if [ "$rc" -ne 0 ] && [ "$BASE_CHANGED" = 1 ] && [ -n "$OLD_BASE" ]; then
        pct exec "$BROKER" -- sh -c \
            "printf '%s\\n' '$OLD_BASE' > /run/homelab-base-rollback.$$ && install -o root -g root -m 0644 /run/homelab-base-rollback.$$ /etc/homelab-bundle-runner/base_revision && rm -f /run/homelab-base-rollback.$$" \
            >/dev/null 2>&1 || true
    fi
    pct exec "$BROKER" -- rm -rf /tmp/homelab-broker-source >/dev/null 2>&1 || true
    rm -rf "$SOURCE_ROOT"
    exit "$rc"
}
trap cleanup EXIT HUP INT TERM

printf '%s' "$BASE_REVISION" | grep -Eq '^[0-9a-f]{40}$' || {
    echo 'PROJECT_WRITER_FAILED: invalid Forgejo base revision' >&2
    exit 1
}
test -f "$ARCHIVE" || { echo 'PROJECT_WRITER_FAILED: source archive absent' >&2; exit 1; }

mkdir "$SOURCE_ROOT"
tar -xzf "$ARCHIVE" -C "$SOURCE_ROOT"
test -x "$SOURCE_ROOT/setup/install-project-document-write.sh"
OLD_BASE=$(pct exec "$BROKER" -- cat /etc/homelab-bundle-runner/base_revision)
[ -n "$OLD_BASE" ] || { echo 'PROJECT_WRITER_FAILED: live base revision absent' >&2; exit 1; }

pct exec "$BROKER" -- rm -rf /tmp/homelab-broker-source
pct exec "$BROKER" -- mkdir -p /tmp/homelab-broker-source/setup
for file in \
    broker_service.py broker_core.py broker_approval_service.py broker_admin.py \
    bundle_verifier.py bundle_runner.py mcp_policy_adapter.py \
    forgejo_mcp_gateway.py project_document_bundle_verifier.py \
    project_document_bundle_runner.py forgejo-mcp-project-write-gateway.service \
    homelab-broker.service \
    setup/install-project-document-write.sh; do
    pct push "$BROKER" "$SOURCE_ROOT/$file" "/tmp/homelab-broker-source/$file" >/dev/null
done

pct exec "$BROKER" -- sh -c \
    "printf '%s\\n' '$BASE_REVISION' > /run/homelab-base-update.$$ && install -o root -g root -m 0644 /run/homelab-base-update.$$ /etc/homelab-bundle-runner/base_revision && rm -f /run/homelab-base-update.$$"
BASE_CHANGED=1
printf 'RUNNER_BASE_UPDATED base=%s\n' "$BASE_REVISION"

pct exec "$BROKER" -- /bin/sh /tmp/homelab-broker-source/setup/install-project-document-write.sh \
    --approved-m2-window /tmp/homelab-broker-source
printf 'PROJECT_GATEWAY_INSTALLED service=forgejo-mcp-project-write\n'

pct exec "$BROKER" -- python3 /opt/homelab-broker/broker_admin.py \
    --database /var/lib/homelab-broker/broker.db \
    enable-forgejo-project-documents --agent-id agent-cloud-bundle
printf 'PROJECT_CAPABILITY_REGISTERED agent=agent-cloud-bundle capability=forgejo.write.project-documents\n'

printf 'PROJECT_WRITER_DEPLOYMENT_COMPLETE\n'
