#!/bin/sh
set -eu

base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for source in "$base_dir"/inbox/*; do
    [ -f "$source" ] || continue
    case "$source" in
        *.csv|*.tsv|*.json|*.xml|*.m3u|*.m3u8)
            status=0
            /usr/bin/python3 "$base_dir/playlist_bridge.py" \
                --execute --max-wait-hours 72 \
                --config "$base_dir/config.json" \
                --report-dir "$base_dir/reports" "$source" || status=$?
            [ "$status" -eq 0 ] || [ "$status" -eq 2 ] || exit "$status"
            ;;
    esac
done
