#!/bin/sh
set -eu

app=/Users/jelliott/Applications/AsterTV-v3-Pilot/Kodi.app
portable="$app/Contents/Resources/Kodi/portable_data"
log="$portable/temp/kodi.log"

if [ ! -f "$portable/.astertv-v3-portable" ]; then
  echo "AsterTV v3 pilot blocked: portable marker is missing" >&2
  exit 1
fi

if ! grep -Fq "special://home/ is mapped to: $portable/" "$log"; then
  echo "AsterTV v3 pilot blocked: running Kodi has not proved portable mode" >&2
  exit 1
fi

rpc() {
  response=$(printf '%s\n' "$1" | nc -w 3 127.0.0.1 9090)
  case "$response" in
    *'"result"'*) printf '%s\n' "$response" ;;
    *) echo "AsterTV v3 pilot JSON-RPC failed: $response" >&2; exit 1 ;;
  esac
}

rpc '{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"skin.asterhome.v3pilot","enabled":true}}'
rpc '{"jsonrpc":"2.0","id":2,"method":"Settings.SetSettingValue","params":{"setting":"lookandfeel.skin","value":"skin.asterhome.v3pilot"}}'
rpc '{"jsonrpc":"2.0","id":3,"method":"GUI.ActivateWindow","params":{"window":"home"}}'

echo "Activated AsterTV v3 pilot skin in the verified portable profile"
