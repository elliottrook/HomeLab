#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
    echo "usage: $0 NAME 'scope.one scope.two' OUTPUT_FILE" >&2
    exit 2
fi

name=$1
scope_string=$2
output_file=$3
admin_password_file=/etc/aster-games/secrets/romm-admin-password
response_file=$(mktemp)
payload_file=$(mktemp)
trap 'rm -f "$response_file" "$payload_file"' EXIT

if [ ! -s "$admin_password_file" ]; then
    echo "RomM administrator credential is unavailable" >&2
    exit 1
fi
if [ -e "$output_file" ]; then
    echo "refusing to replace existing token file" >&2
    exit 1
fi

python3 - "$name" "$scope_string" "$payload_file" <<'PY'
import json
import sys

name, scopes, destination = sys.argv[1:]
with open(destination, "w", encoding="utf-8") as handle:
    json.dump({"name": name, "scopes": scopes.split(), "expires_in": None}, handle)
PY

password=$(cat "$admin_password_file")
status=$(
    curl -sS -o "$response_file" -w '%{http_code}' \
        -u "aster-admin:$password" \
        -H 'Content-Type: application/json' \
        --data-binary "@$payload_file" \
        http://127.0.0.1:8080/api/client-tokens
)
if [ "$status" != 201 ]; then
    echo "RomM client-token creation failed with HTTP $status" >&2
    exit 1
fi

umask 077
jq -er '.raw_token' "$response_file" >"$output_file"
chmod 0400 "$output_file"
jq -r '"created RomM token: id=\(.id) name=\(.name) scopes=\(.scopes|join(","))"' "$response_file"
