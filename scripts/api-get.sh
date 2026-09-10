#!/usr/bin/env bash
# Read-only GET wrapper for the Authentik/NPM HTTPS APIs.
#
# Structurally read-only: only ever issues a curl GET (no -X, -d, -F, -T,
# etc. accepted), and only against the allowlisted API hosts/paths below.
# This is what permissions.allow references so read-only discovery work
# doesn't need a per-call approval prompt, while state-changing calls
# still require the full Bash tool prompt (see docs/projects/Authentik-Rollout.md
# and CLAUDE.md's Sandbox network access section).
#
# Auth: pass the bearer token via API_TOKEN in the environment. Never
# pass it as a command-line argument (it would land in process listings).
#
# Usage: api-get.sh <url> [extra safe curl args, e.g. -o outfile]

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: api-get.sh <url> [curl-args]" >&2
  exit 1
fi

url="$1"
shift

case "$url" in
  https://auth.elliottrook.com/api/*|https://proxy.elliottrook.com/api/*) ;;
  *)
    echo "api-get.sh: URL not allowed (must be https://auth.elliottrook.com/api/... or https://proxy.elliottrook.com/api/...): $url" >&2
    exit 1
    ;;
esac

for arg in "$@"; do
  case "$arg" in
    -X|--request|-d|--data*|-F|--form*|-T|--upload-file|-u|--user|--url)
      echo "api-get.sh: disallowed argument: $arg (this wrapper is GET-only)" >&2
      exit 1
      ;;
  esac
done

exec curl -sS -H "Authorization: Bearer ${API_TOKEN:?API_TOKEN not set}" "$url" "$@"
