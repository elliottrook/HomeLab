#!/usr/bin/env bash
# Builds AsterCompanion.app from the Swift package, for real (non-Xcode)
# testing of the passkey login flow, which needs a genuine .app bundle
# with a registered URL scheme.
set -euo pipefail
cd "$(dirname "$0")"

CONFIG="${1:-debug}"
swift build -c "$CONFIG"

BIN_PATH=$(swift build -c "$CONFIG" --show-bin-path)
APP_DIR="$BIN_PATH/AsterCompanion.app"

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"
cp "$BIN_PATH/AsterCompanion" "$APP_DIR/Contents/MacOS/AsterCompanion"
cp Info.plist "$APP_DIR/Contents/Info.plist"

# Register the URL scheme with Launch Services so the OS routes the
# aster-companion://callback redirect back to this app.
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_DIR"

echo "Built: $APP_DIR"
