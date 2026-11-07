#!/bin/sh
set -eu

password_file=${1:-/etc/aster-games/secrets/romm-admin-password}
response_file=$(mktemp)
cookie_file=$(mktemp)
trap 'rm -f "$response_file" "$cookie_file"' EXIT

if [ -e "$password_file" ]; then
    echo "refusing to replace existing RomM administrator credential" >&2
    exit 1
fi

umask 077
openssl rand -base64 36 | tr -d '\n' >"$password_file"
password=$(cat "$password_file")
curl -fsS -c "$cookie_file" http://127.0.0.1:8080/api/setup/library >/dev/null
csrf_token=$(awk '$6 == "romm_csrftoken" {print $7}' "$cookie_file")
if [ -z "$csrf_token" ]; then
    rm -f "$password_file"
    echo "RomM did not issue a setup CSRF token" >&2
    exit 1
fi

status=$(
    jq -n \
        --arg username "aster-admin" \
        --arg email "aster-games-admin@home.internal" \
        --arg password "$password" \
        '{username:$username,email:$email,password:$password,role:"ADMIN"}' |
        curl -sS -o "$response_file" -w '%{http_code}' \
            -H 'Content-Type: application/json' \
            -H "Cookie: romm_csrftoken=$csrf_token" \
            -H "x-csrftoken: $csrf_token" \
            --data-binary @- \
            http://127.0.0.1:8080/api/users
)

if [ "$status" != 201 ]; then
    rm -f "$password_file"
    echo "RomM administrator creation failed with HTTP $status" >&2
    exit 1
fi

python3 - "$response_file" <<'PY'
import json
import sys

document = json.load(open(sys.argv[1], encoding="utf-8"))
print(
    "created RomM administrator: "
    f"id={document.get('id')} username={document.get('username')} "
    f"role={document.get('role')}"
)
PY
