#!/bin/sh
# Run on the Proxmox host. Read-only; bounds and prefilters B60-relevant lines.
set -eu
if [ "$#" -ne 2 ]; then
    printf 'usage: %s START_EPOCH END_EPOCH\n' "$0" >&2
    exit 2
fi
case "$1:$2" in *[!0-9:]*|:*|*:) exit 2 ;; esac
journalctl -k --since="@$1" --until="@$2" --no-pager -o short-iso 2>/dev/null |
    grep -Ei '\b(xe|drm|oom|out of memory|device.{0,20}lost|reset|hang)\b' |
    tail -n 500 || true
