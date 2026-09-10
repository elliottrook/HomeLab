#!/bin/sh
# Run as root inside the Forgejo LXC after installing the report service files.
set -eu

forgejo=/usr/local/bin/forgejo
config=/etc/forgejo/app.ini
database=/var/lib/forgejo/data/forgejo.db
api=http://127.0.0.1:3000/api/v1
service_user=aster-readonly
service_token_name=aster-source-report
provision_token_name=aster-source-report-provision-20260909
admin_header=/run/aster-forgejo-admin-header
service_header=/run/aster-forgejo-service-header

if ! sqlite3 "$database" "select 1 from user where name='$service_user';" | grep -qx 1; then
    runuser -u git -- "$forgejo" admin user create --config "$config" \
        --username "$service_user" --email aster-readonly@localhost.invalid \
        --random-password --restricted >/dev/null
fi

account_state=$(sqlite3 -separator : "$database" \
    "select is_active,is_admin,is_restricted,must_change_password,allow_git_hook,allow_import_local from user where name='$service_user';")
[ "$account_state" = "1:0:1:0:0:0" ] || [ "$account_state" = "1:0:1:1:0:0" ] || {
    echo "Forgejo Aster account does not match the restricted profile" >&2
    exit 1
}

install -d -o root -g aster-forgejo-report -m 0750 /etc/aster-forgejo-report
profile=$(sqlite3 -separator : "$database" \
    "select must_change_password,allow_create_organization,max_repo_creation from user where name='$service_user';")
if [ "$profile" != "0:0:0" ]; then
    admin_token=$(runuser -u git -- "$forgejo" admin user generate-access-token \
        --config "$config" --username jason --token-name "$provision_token_name" \
        --scopes write:admin --raw)
    umask 077
    printf 'Authorization: token %s\n' "$admin_token" > "$admin_header"
    cleanup_profile() {
        rm -f "$admin_header"
        sqlite3 "$database" "pragma busy_timeout=5000; delete from access_token where name='$provision_token_name' and uid=(select id from user where name='jason');" >/dev/null
    }
    trap cleanup_profile EXIT HUP INT TERM
    status=$(curl -sS -o /run/aster-forgejo-user-response \
        -w '%{http_code}' -X PATCH -H "@$admin_header" \
        -H 'Content-Type: application/json' \
        --data '{"must_change_password":false,"allow_create_organization":false,"max_repo_creation":0}' \
        "$api/admin/users/$service_user")
    [ "$status" = 200 ] || {
        echo "Forgejo rejected the restricted account profile" >&2
        exit 1
    }
    rm -f /run/aster-forgejo-user-response
    cleanup_profile
    trap - EXIT HUP INT TERM
    unset admin_token
fi

if [ ! -s /etc/aster-forgejo-report/token ]; then
    admin_token=$(runuser -u git -- "$forgejo" admin user generate-access-token \
        --config "$config" --username jason --token-name "$provision_token_name" \
        --scopes write:admin,write:repository,write:user --raw)
    umask 077
    printf 'Authorization: token %s\n' "$admin_token" > "$admin_header"
    cleanup() {
        rm -f "$admin_header"
        sqlite3 "$database" "pragma busy_timeout=5000; delete from access_token where name='$provision_token_name' and uid=(select id from user where name='jason');" >/dev/null
    }
    trap cleanup EXIT HUP INT TERM
    status=$(curl -sS -o /run/aster-forgejo-user-response \
        -w '%{http_code}' -X PATCH -H "@$admin_header" \
        -H 'Content-Type: application/json' \
        --data '{"must_change_password":false,"allow_create_organization":false,"max_repo_creation":0}' \
        "$api/admin/users/$service_user")
    [ "$status" = 200 ] || {
        echo "Forgejo rejected the restricted account profile" >&2
        exit 1
    }
    rm -f /run/aster-forgejo-user-response
    status=$(curl -sS -o /run/aster-forgejo-collaborator-response \
        -w '%{http_code}' -X PUT -H "@$admin_header" \
        -H 'Content-Type: application/json' --data '{"permission":"read"}' \
        "$api/repos/jason/homelab/collaborators/$service_user")
    [ "$status" = 204 ] || {
        echo "Forgejo rejected the read-only collaborator assignment" >&2
        exit 1
    }
    rm -f /run/aster-forgejo-collaborator-response

    service_token=$(runuser -u git -- "$forgejo" admin user generate-access-token \
        --config "$config" --username "$service_user" --token-name "$service_token_name" \
        --scopes read:repository,read:issue,read:user --raw)
    umask 0137
    printf '%s\n' "$service_token" > /etc/aster-forgejo-report/token
    chown root:aster-forgejo-report /etc/aster-forgejo-report/token
    unset service_token
    cleanup
    trap - EXIT HUP INT TERM
    unset admin_token
fi

account_state=$(sqlite3 -separator : "$database" \
    "select must_change_password,allow_create_organization,max_repo_creation from user where name='$service_user';")
[ "$account_state" = "0:0:0" ] || {
    echo "Forgejo Aster account can still create repositories or organizations" >&2
    exit 1
}

permission=$(sqlite3 "$database" "select a.mode from access a join user u on u.id=a.user_id join repository r on r.id=a.repo_id where u.name='$service_user' and r.owner_id=(select id from user where name='jason') and r.name='homelab';")
[ "$permission" = 1 ] || {
    echo "Forgejo collaborator is not read-only" >&2
    exit 1
}
scope=$(sqlite3 "$database" "select scope from access_token t join user u on u.id=t.uid where u.name='$service_user' and t.name='$service_token_name';")
[ "$scope" = "read:issue,read:repository,read:user" ] || {
    echo "Forgejo token scope is not the approved read-only set" >&2
    exit 1
}
umask 077
printf 'Authorization: token ' > "$service_header"
sed -n '1p' /etc/aster-forgejo-report/token >> "$service_header"
printf '\n' >> "$service_header"
trap 'rm -f "$service_header"' EXIT HUP INT TERM
status=$(curl -sS -o /dev/null -w '%{http_code}' -H "@$service_header" \
    "$api/repos/jason/homelab")
rm -f "$service_header"
trap - EXIT HUP INT TERM
[ "$status" = 200 ] || {
    echo "Forgejo read-only token verification failed" >&2
    exit 1
}
echo "source=forgejo identity=aster-readonly permission=read token_scopes=read-only status=verified"
