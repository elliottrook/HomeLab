#!/bin/sh
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
archive="$repo/services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
archive_sha=e813de8a74af769ebbfeb744ad65249760292f647dc2d91c4bafb9fc7ba83cf7
app=/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app
portable="$app/Contents/Resources/Kodi/portable_data"
addons="$portable/addons"
target="$addons/skin.asterhome.v3pilot"
next="$addons/.skin.asterhome.v3pilot.next"
previous="$addons/.skin.asterhome.v3pilot.previous"
overlay="$repo/services/kodi/astertv-v3/overlay/skin.asterhome.v3pilot"
patches="$repo/services/kodi/astertv-v3/patches"
marker_source="$repo/services/kodi/astertv-v3/pilot/portable-marker"
marker="$portable/.astertv-v3-portable"
keymap_source="$repo/services/kodi/astertv-v3/pilot/keymaps/astertv-v3-pilot.xml"
keymap_target="$portable/userdata/keymaps/astertv-v3-pilot.xml"

case "$portable" in
  /Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app/Contents/Resources/Kodi/portable_data) ;;
  *) echo "Refusing unsafe portable path: $portable" >&2; exit 1 ;;
esac

test -f "$archive"
actual_sha=$(shasum -a 256 "$archive" | awk '{print $1}')
if [ "$actual_sha" != "$archive_sha" ]; then
  echo "Accepted v2 archive digest mismatch" >&2
  exit 1
fi

version=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  "$app/Contents/Info.plist")
if [ "$version" != "22.0.rc1" ]; then
  echo "Expected Kodi 22.0.rc1, found $version" >&2
  exit 1
fi

stage=$(mktemp -d /private/tmp/astertv-v3-skin.XXXXXX)
cleanup() {
  rm -rf "$stage"
}
trap cleanup EXIT HUP INT TERM

tar -xzf "$archive" -C "$stage" \
  aster-v2-package/lab-addon-snapshot/skin.asterhome
mv "$stage/aster-v2-package/lab-addon-snapshot/skin.asterhome" \
  "$stage/skin.asterhome.v3pilot"
ditto "$overlay" "$stage/skin.asterhome.v3pilot"
for patch_file in "$patches"/*.patch; do
  patch -d "$stage/skin.asterhome.v3pilot" -p1 < "$patch_file"
done
python3 "$repo/services/kodi/astertv-v3/apply_art_title_focus.py" \
  "$stage/skin.asterhome.v3pilot"

xmllint --noout "$stage/skin.asterhome.v3pilot/addon.xml"
xmllint --noout "$stage/skin.asterhome.v3pilot/1080i/Home.xml"
xmllint --noout "$stage/skin.asterhome.v3pilot/1080i/Includes.xml"
xmllint --noout "$stage/skin.asterhome.v3pilot/1080i/IncludesV3.xml"
xmllint --noout "$stage/skin.asterhome.v3pilot/1080i/custom_1190_v3language.xml"
xmllint --noout "$stage/skin.asterhome.v3pilot/1080i/custom_1191_youtube_rework.xml"
xmllint --noout "$stage/skin.asterhome.v3pilot/1080i/custom_1192_tile_gallery.xml"
xmllint --noout "$keymap_source"

mkdir -p "$addons" "$portable/userdata/keymaps"
ditto "$marker_source" "$marker"
ditto "$keymap_source" "$keymap_target"

rm -rf "$next"
ditto "$stage/skin.asterhome.v3pilot" "$next"
rm -rf "$previous"
if [ -d "$target" ]; then
  mv "$target" "$previous"
fi
mv "$next" "$target"

echo "Prepared AsterTV v3 pilot skin at $target"

