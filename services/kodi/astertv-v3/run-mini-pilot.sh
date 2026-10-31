#!/bin/sh
set -eu

app=/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app
resources="$app/Contents/Resources/Kodi"
portable="$resources/portable_data"
marker="$portable/.astertv-v3-portable"
standard=/Users/jelliott/Library/Application\ Support/Kodi

if [ ! -x "$app/Contents/MacOS/Kodi" ]; then
  echo "AsterTV v3 pilot blocked: dedicated Kodi executable is missing" >&2
  exit 1
fi

version=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  "$app/Contents/Info.plist")
if [ "$version" != "22.0.rc1" ]; then
  echo "AsterTV v3 pilot blocked: expected Kodi 22.0.rc1, found $version" >&2
  exit 1
fi

if [ ! -d "$portable" ] || [ ! -f "$marker" ]; then
  echo "AsterTV v3 pilot blocked: portable-data boundary is not provisioned" >&2
  exit 1
fi

if [ "$portable" = "$standard" ] || [ "$portable" = "/" ]; then
  echo "AsterTV v3 pilot blocked: unsafe portable-data path" >&2
  exit 1
fi

exec /usr/bin/open -n "$app" --args -p

