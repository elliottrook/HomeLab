#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output=${1:-"$repo_root/aster-knowledge.tar.gz"}

case "$output" in
    /*) ;;
    *) output="$PWD/$output" ;;
esac

files='CLAUDE.md
README.md
docs/01-Architecture.md
docs/02-IP-Addressing.md
docs/03-Hardware-Inventory.md
docs/05-Backups.md
docs/AI-Hermes-Second-Brain.md
docs/Aster-Operations.md
docs/projects/Local-AI.md'

for relative in $files; do
    if [ ! -f "$repo_root/$relative" ]; then
        printf 'Missing curated knowledge source: %s\n' "$relative" >&2
        exit 1
    fi
done

mkdir -p "$(dirname -- "$output")"
COPYFILE_DISABLE=1 tar --no-mac-metadata --no-xattrs -C "$repo_root" -czf "$output" $files
printf 'Created %s\n' "$output"
