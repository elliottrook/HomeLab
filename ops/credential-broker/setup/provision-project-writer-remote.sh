#!/bin/sh
# Run on the Proxmox host. Creates the dedicated Forgejo PAT, stores it in
# OpenBao, creates the bounded AppRole, and installs only the AppRole JSON on
# LXC 104. Secret values remain in protected temporary files and pipes.
set -eu
umask 077

FORGEJO=108
BROKER=104
OPENBAO=117
TOKEN_USER=ai-pam-project-docs
TOKEN_NAME=ai-pam-project-docs-20261013
ROLE_NAME=hlabroker-forgejo-project-write
POLICY_NAME=hlabroker-forgejo-project-write
SECRET_PATH=secret/data/ai-pam/forgejo-mcp-project-write
ROOT_FILE=/run/openbao-human-root-token
RUN_ID=$$
TMP_ROOT=/tmp/homelab-project-writer.$RUN_ID
PAT_HOST=$TMP_ROOT/forgejo-pat
POLICY_HOST=$TMP_ROOT/policy.hcl
BAO_HELPER_HOST=$TMP_ROOT/provision-bao.sh
CREDENTIAL_HOST=$TMP_ROOT/approle.json
PAT_GUEST=/run/homelab-project-writer-pat.$RUN_ID
POLICY_GUEST=/run/homelab-project-writer-policy.$RUN_ID
BAO_HELPER_GUEST=/run/homelab-project-writer-bao.$RUN_ID
CREDENTIAL_GUEST=/run/homelab-project-writer-approle.$RUN_ID
CREDENTIAL_TARGET=/etc/homelab-broker/openbao-project-write-approle.json
pat_created=0
role_created=0
credential_installed=0
completed=0

cleanup() {
    rc=$?
    if [ "$completed" != 1 ]; then
        if [ "$credential_installed" = 1 ]; then
            pct exec "$BROKER" -- rm -f "$CREDENTIAL_TARGET" >/dev/null 2>&1 || true
        fi
        if [ "$role_created" = 1 ]; then
            pct exec "$OPENBAO" -- sh -c \
                "BAO_ADDR=https://127.0.0.1:8200 BAO_CACERT=/opt/openbao/tls/tls.crt BAO_TOKEN=\$(cat '$ROOT_FILE') bao delete 'auth/approle/role/$ROLE_NAME' >/dev/null 2>&1 || true" \
                >/dev/null 2>&1 || true
            pct exec "$OPENBAO" -- sh -c \
                "BAO_ADDR=https://127.0.0.1:8200 BAO_CACERT=/opt/openbao/tls/tls.crt BAO_TOKEN=\$(cat '$ROOT_FILE') bao kv metadata delete -mount=secret ai-pam/forgejo-mcp-project-write >/dev/null 2>&1 || true" \
                >/dev/null 2>&1 || true
        fi
        if [ "$pat_created" = 1 ]; then
            # The token name was checked absent before creation. Remove only
            # this newly-created row if a later step fails.
            pct exec "$FORGEJO" -- sqlite3 /var/lib/forgejo/data/forgejo.db \
                "delete from access_token where uid=(select id from user where lower_name='$TOKEN_USER') and name='$TOKEN_NAME';" \
                >/dev/null 2>&1 || true
        fi
    fi
    pct exec "$OPENBAO" -- rm -f "$PAT_GUEST" "$POLICY_GUEST" "$BAO_HELPER_GUEST" "$CREDENTIAL_GUEST" >/dev/null 2>&1 || true
    rm -rf "$TMP_ROOT"
    exit "$rc"
}
trap cleanup EXIT HUP INT TERM

fail() {
    printf '%s\n' "PROJECT_WRITER_FAILED: $1" >&2
    exit 1
}

mkdir "$TMP_ROOT"

pct exec "$OPENBAO" -- test -s "$ROOT_FILE" >/dev/null 2>&1 ||
    fail 'protected human root-token handoff is absent'

access=$(pct exec "$FORGEJO" -- sqlite3 -readonly -separator '|' \
    /var/lib/forgejo/data/forgejo.db \
    "select u.lower_name,r.lower_name,a.mode from access a join user u on u.id=a.user_id join repository r on r.id=a.repo_id where u.lower_name='$TOKEN_USER' and r.lower_name='homelab';")
[ "$access" = "$TOKEN_USER|homelab|2" ] || fail 'writer identity or repository access is not the expected mode'

existing_token=$(pct exec "$FORGEJO" -- sqlite3 -readonly \
    /var/lib/forgejo/data/forgejo.db \
    "select count(*) from access_token where uid=(select id from user where lower_name='$TOKEN_USER') and name='$TOKEN_NAME';")
[ "$existing_token" = 0 ] || fail 'token name already exists; refusing to overwrite or duplicate it'

cat > "$POLICY_HOST" <<'EOF'
path "secret/data/ai-pam/forgejo-mcp-project-write" {
  capabilities = ["read"]
}
EOF

cat > "$BAO_HELPER_HOST" <<EOF
#!/bin/sh
set -eu
umask 077
BAO_ADDR=https://127.0.0.1:8200
BAO_CACERT=/opt/openbao/tls/tls.crt
ROOT=$ROOT_FILE
PAT=$PAT_GUEST
POLICY=$POLICY_GUEST
ROLE=$ROLE_NAME
POLICY_NAME=$POLICY_NAME
SECRET=$SECRET_PATH
CREDENTIAL=$CREDENTIAL_GUEST

test -s "\$ROOT" && test -s "\$PAT" && test -s "\$POLICY"
root_token=\$(cat "\$ROOT")
export BAO_ADDR BAO_CACERT BAO_TOKEN=\$root_token

if bao read -format=json "\$SECRET" >/dev/null 2>&1; then
    echo 'existing OpenBao secret path' >&2
    exit 1
fi
if bao read -format=json "auth/approle/role/\$ROLE" >/dev/null 2>&1; then
    echo 'existing OpenBao AppRole' >&2
    exit 1
fi

bao policy write "\$POLICY_NAME" "\$POLICY" >/dev/null 2>&1
echo 'OPENBAO_POLICY_OK'
# The gateway logs in once per MCP request; keep the protected AppRole
# SecretID reusable while keeping each issued OpenBao token short-lived.
bao write "auth/approle/role/\$ROLE" \
    token_policies="\$POLICY_NAME" \
    token_ttl=5m token_max_ttl=30m token_no_default_policy=true \
    secret_id_num_uses=0 secret_id_ttl=0 \
    secret_id_bound_cidrs=192.168.70.10/32 bind_secret_id=true \
    >/dev/null 2>&1
echo 'OPENBAO_APPROLE_OK'
role_id=\$(bao read -field=role_id "auth/approle/role/\$ROLE/role-id")
secret_id=\$(bao write -f -field=secret_id "auth/approle/role/\$ROLE/secret-id")
[ -n "\$role_id" ] && [ -n "\$secret_id" ]
echo 'OPENBAO_APPROLE_CREDENTIAL_OK'

jq -n --rawfile token "\$PAT" '{token: \$token}' > /run/homelab-project-writer-secret.$$
bao kv put -mount=secret ai-pam/forgejo-mcp-project-write \
    @/run/homelab-project-writer-secret.$$ >/dev/null 2>&1
rm -f /run/homelab-project-writer-secret.$$
echo 'OPENBAO_SECRET_OK'

jq -n --arg role_id "\$role_id" --arg secret_id "\$secret_id" \
    '{role_id: \$role_id, secret_id: \$secret_id}' > "\$CREDENTIAL"
chmod 0600 "\$CREDENTIAL"
test -s "\$CREDENTIAL"
echo 'OPENBAO_HANDOFF_OK'
EOF
chmod 0700 "$BAO_HELPER_HOST"

printf 'PROJECT_WRITER_PROVISIONING starting\n'

if ! pct exec "$FORGEJO" -- runuser -u git -- /usr/local/bin/forgejo \
    --config /etc/forgejo/app.ini --work-path /var/lib/forgejo \
    admin user generate-access-token \
    --username "$TOKEN_USER" --token-name "$TOKEN_NAME" \
    --scopes 'read:repository,write:repository' --raw > "$PAT_HOST" 2>/dev/null; then
    fail 'Forgejo PAT creation failed'
fi
tr -d '\r\n' < "$PAT_HOST" > "$PAT_HOST.clean"
mv "$PAT_HOST.clean" "$PAT_HOST"
chmod 0600 "$PAT_HOST"
test -s "$PAT_HOST" || fail 'Forgejo PAT creation returned no value'
pat_created=1
printf 'FORGEJO_PAT_CREATED user=%s scope=read:repository,write:repository\n' "$TOKEN_USER"

pct push "$OPENBAO" "$PAT_HOST" "$PAT_GUEST" >/dev/null
pct push "$OPENBAO" "$POLICY_HOST" "$POLICY_GUEST" >/dev/null
pct push "$OPENBAO" "$BAO_HELPER_HOST" "$BAO_HELPER_GUEST" >/dev/null
pct exec "$OPENBAO" -- chmod 0600 "$PAT_GUEST" "$POLICY_GUEST" "$BAO_HELPER_GUEST"

role_created=1
if ! pct exec "$OPENBAO" -- /bin/sh "$BAO_HELPER_GUEST"; then
    fail 'OpenBao policy, AppRole or secret write failed'
fi
printf 'OPENBAO_SECRET_STORED path=%s\n' "$SECRET_PATH"

pct pull "$OPENBAO" "$CREDENTIAL_GUEST" "$CREDENTIAL_HOST" >/dev/null
chmod 0600 "$CREDENTIAL_HOST"
test -s "$CREDENTIAL_HOST" || fail 'OpenBao AppRole credential handoff was empty'
pct push "$BROKER" "$CREDENTIAL_HOST" "$CREDENTIAL_TARGET" >/dev/null
credential_installed=1
printf 'APPROLE_CREDENTIAL_INSTALLED target=%s\n' "$CREDENTIAL_TARGET"

completed=1
printf 'PROJECT_WRITER_PROVISIONING_COMPLETE role=%s\n' "$ROLE_NAME"
