#!/bin/sh
# stdin is a four-line secret payload supplied by the local wrapper. This
# script must never print those lines or include them in process arguments.
set -eu
umask 077

BAO_ADDR=https://127.0.0.1:8200
BAO_CACERT=/opt/openbao/tls/tls.crt
ROOT_TOKEN_FILE=/run/openbao-human-root-token
TMP_ROOT=/run/openbao-human-root-ceremony.$$
operator_token=
ceremony_complete=0
mkdir "$TMP_ROOT"

cleanup() {
    rc=$?
    if [ "${ceremony_complete:-0}" != 1 ] && [ -n "${operator_token:-}" ]; then
        BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
            bao operator generate-root -cancel -non-interactive >/dev/null 2>&1 || true
    fi
    if [ -n "${operator_token:-}" ]; then
        BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
            bao token revoke -self -non-interactive >/dev/null 2>&1 || true
    fi
    rm -rf "$TMP_ROOT"
    unset role_id secret_id share result encoded_token root_token
    exit "$rc"
}
trap cleanup EXIT HUP INT TERM

fail() {
    printf '%s\n' "CEREMONY_FAILED: $1" >&2
    exit 1
}

read_line() {
    IFS= read -r REPLY || fail 'secret payload was incomplete'
}

read_line
role_id=$REPLY
read_line
secret_id=$REPLY
[ -n "$role_id" ] || fail 'role_id was empty'
[ -n "$secret_id" ] || fail 'secret_id was empty'

printf '%s' "$role_id" > "$TMP_ROOT/role_id"
printf '%s' "$secret_id" > "$TMP_ROOT/secret_id"
jq -n --rawfile role_id "$TMP_ROOT/role_id" --rawfile secret_id "$TMP_ROOT/secret_id" \
    '{role_id: $role_id, secret_id: $secret_id}' > "$TMP_ROOT/login.json"
unset role_id secret_id REPLY

login_json=$(BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" \
    bao write -format=json auth/approle/login @"$TMP_ROOT/login.json" 2>/dev/null) \
    || fail 'AppRole login was rejected'
operator_token=$(printf '%s' "$login_json" | jq -r '.auth.client_token // empty')
[ -n "$operator_token" ] || fail 'AppRole login returned no client token'
unset login_json

if test -e "$ROOT_TOKEN_FILE"; then
    fail 'root-token handoff already exists; refusing to overwrite it'
fi

status_json=$(BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
    bao operator generate-root -status -format=json -non-interactive 2>/dev/null) \
    || fail 'could not read root-ceremony status'
existing_progress=$(printf '%s' "$status_json" | jq -r '.progress // 0')
[ "$existing_progress" = 0 ] || fail 'another root ceremony is already in progress'
unset status_json existing_progress

otp_json=$(BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
    bao operator generate-root -generate-otp -format=json -non-interactive 2>/dev/null) \
    || fail 'could not generate an OpenBao-compatible OTP'
otp=$(printf '%s' "$otp_json" | jq -r '.otp // empty' 2>/dev/null || true)
[ -n "$otp" ] || otp=$(printf '%s' "$otp_json" | tr -d '\r\n')
[ -n "$otp" ] || fail 'OpenBao returned no OTP'
unset otp_json
if ! init_json=$(BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
    bao operator generate-root -init -otp="$otp" -format=json -non-interactive \
    2>"$TMP_ROOT/init.stderr"); then
    code=$(sed -n 's/.*Code: \([0-9][0-9][0-9]\).*/HTTP \1/p' "$TMP_ROOT/init.stderr" | head -n 1)
    message=$(sed -n 's/^\* //p' "$TMP_ROOT/init.stderr" | tr '\n' ' ')
    case "$message" in
        *token*|*otp*|*nonce*|*key*|*secret*) message='redacted OpenBao error' ;;
    esac
    [ -n "$code" ] || code='OpenBao rejected request'
    [ -n "$message" ] || message='no detail returned'
    fail "could not start root ceremony ($code; $message)"
fi
nonce=$(printf '%s' "$init_json" | jq -r '.nonce // empty')
required=$(printf '%s' "$init_json" | jq -r '.required // 0')
[ -n "$nonce" ] || fail 'root ceremony returned no nonce'
[ "$required" = 2 ] || fail 'unexpected recovery threshold'
printf 'CEREMONY_STARTED threshold=2\n'
unset init_json

count=0
while [ "$count" -lt 2 ]; do
    read_line
    share=$REPLY
    [ -n "$share" ] || fail 'recovery share was empty'
    if ! result=$(printf '%s\n' "$share" | \
        BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
        bao operator generate-root -otp="$otp" -nonce="$nonce" -format=json - \
        2>"$TMP_ROOT/share-$count.stderr"); then
        code=$(sed -n 's/.*Code: \([0-9][0-9][0-9]\).*/HTTP \1/p' "$TMP_ROOT/share-$count.stderr" | head -n 1)
        message=$(sed -n 's/^\* //p' "$TMP_ROOT/share-$count.stderr" | tr '\n' ' ')
        case "$message" in
            *token*|*otp*|*nonce*|*secret*) message='redacted OpenBao error' ;;
        esac
        [ -n "$code" ] || code='OpenBao rejected request'
        [ -n "$message" ] || message='no detail returned'
        fail "recovery share $((count + 1)) failed ($code; $message)"
    fi
    unset share REPLY
    progress=$(printf '%s' "$result" | jq -r '.progress // 0')
    [ "$progress" -gt "$count" ] 2>/dev/null || fail 'recovery share did not advance the ceremony'
    count=$progress
    printf 'CEREMONY_PROGRESS %s/2\n' "$count"
    encoded_token=$(printf '%s' "$result" | jq -r '.encoded_token // empty')
    unset result progress
done

[ -n "${encoded_token:-}" ] || fail 'ceremony completed without an encoded token'
root_token=$(printf '%s' "$encoded_token" | \
    BAO_ADDR="$BAO_ADDR" BAO_CACERT="$BAO_CACERT" BAO_TOKEN="$operator_token" \
    bao operator generate-root -decode=- -otp="$otp" 2>/dev/null | \
    tr -d '\r\n') || fail 'could not decode the generated root token'
[ -n "$root_token" ] || fail 'decoded root token was empty'
case "$root_token" in
    *[!A-Za-z0-9._-]*) fail 'decoded root token had an unexpected format' ;;
esac
printf '%s' "$root_token" > "$ROOT_TOKEN_FILE"
chmod 0600 "$ROOT_TOKEN_FILE"
test -s "$ROOT_TOKEN_FILE" || fail 'root-token handoff file was not created'
ceremony_complete=1
printf 'CEREMONY_COMPLETE\n'
