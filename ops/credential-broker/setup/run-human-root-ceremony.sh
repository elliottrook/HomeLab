#!/bin/sh
# Prompt locally, then send opaque values over noninteractive SSH. No
# credential or recovery share is placed in a command argument or log.
set -eu
umask 077

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REMOTE_HELPER="$SCRIPT_DIR/run-human-root-ceremony-remote.sh"
REMOTE_HOST=root@192.168.50.10
REMOTE_STAGE=/tmp/homelab-human-root-remote.$$
REMOTE_PATH=/run/homelab-human-root-remote.$$
LOCAL_TMP=$(mktemp -d "${TMPDIR:-/tmp}/homelab-human-root.XXXXXX")
PAYLOAD="$LOCAL_TMP/payload"
TTY_STATE=

cleanup() {
    rc=$?
    if [ -n "$TTY_STATE" ]; then
        stty "$TTY_STATE" 2>/dev/null || true
    fi
    ssh -T -o BatchMode=yes "$REMOTE_HOST" \
        "pct exec 117 -- /bin/sh -c 'rm -f \"$REMOTE_PATH\"'; rm -f \"$REMOTE_STAGE\"" \
        >/dev/null 2>&1 || true
    rm -rf "$LOCAL_TMP"
    exit "$rc"
}
trap cleanup EXIT HUP INT TERM

fail() {
    printf '%s\n' "CEREMONY_FAILED: $1" >&2
    exit 1
}

read_secret() {
    prompt=$1
    printf '%s' "$prompt"
    TTY_STATE=$(stty -g) || fail 'terminal is unavailable'
    stty -echo || fail 'could not disable terminal echo'
    if ! IFS= read -r value; then
        stty "$TTY_STATE" 2>/dev/null || true
        TTY_STATE=
        fail 'input was interrupted'
    fi
    stty "$TTY_STATE" || fail 'could not restore terminal echo'
    TTY_STATE=
    printf '\n'
    REPLY=$value
    unset value
}

: > "$PAYLOAD"
read_secret 'Human ceremony AppRole role_id: '
printf '%s\n' "$REPLY" >> "$PAYLOAD"
read_secret 'Human ceremony AppRole secret_id: '
printf '%s\n' "$REPLY" >> "$PAYLOAD"
read_secret 'Recovery share 1 of 2: '
printf '%s\n' "$REPLY" >> "$PAYLOAD"
read_secret 'Recovery share 2 of 2: '
printf '%s\n' "$REPLY" >> "$PAYLOAD"
unset REPLY

printf 'CEREMONY_TRANSPORT starting\n'
scp -q -o BatchMode=yes "$REMOTE_HELPER" "$REMOTE_HOST:$REMOTE_STAGE" \
    || fail 'could not stage the noninteractive remote helper'
ssh -T -o BatchMode=yes "$REMOTE_HOST" \
    "pct push 117 '$REMOTE_STAGE' '$REMOTE_PATH' >/dev/null && rm -f '$REMOTE_STAGE'" \
    || fail 'could not install the remote helper'

ssh -T -o BatchMode=yes "$REMOTE_HOST" \
    "pct exec 117 -- /bin/sh '$REMOTE_PATH'" < "$PAYLOAD"
