#!/bin/sh
# Apply the approved stone-framed Aster icon to a disposable macOS Kodi app.
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /absolute/path/to/Kodi-test.app" >&2
  exit 2
fi

app=$1
case "$app" in
  /*.app) ;;
  *) echo "Pass an absolute .app path" >&2; exit 2 ;;
esac

bundle_id=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app/Contents/Info.plist")
icon_name=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIconFile' "$app/Contents/Info.plist")
if [ "$bundle_id" != org.xbmc.kodi ] || [ "$icon_name" != kodi.icns ]; then
  echo "Not the expected macOS Kodi bundle/icon; leaving it unchanged" >&2
  exit 2
fi

icon="$app/Contents/Resources/kodi.icns"
backup="${app%.app}.original-kodi.icns"
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_icon="$source_dir/media/aster-icon-512.png"

if [ ! -f "$icon" ] || [ ! -f "$source_icon" ]; then
  echo "Kodi icon or approved Aster source is missing" >&2
  exit 2
fi
if [ ! -e "$backup" ]; then
  cp -p "$icon" "$backup"
fi

temporary=$(mktemp "${TMPDIR:-/tmp}/aster-kodi-dock.XXXXXX.icns")
trap 'rm -f "$temporary"' EXIT HUP INT TERM
sips -s format icns "$source_icon" --out "$temporary" >/dev/null
cp "$temporary" "$icon"
touch "$app"
if killall Dock >/dev/null 2>&1; then
  echo "Restarted Dock to refresh its cached app icon"
else
  echo "Dock refresh was unavailable; run 'killall Dock' in a normal Mac shell if its icon stays stale" >&2
fi
echo "Installed approved Aster Dock icon: $icon"
echo "Original Kodi icon backed up at: $backup"
echo "To restore: cp '$backup' '$icon'; touch '$app'"
