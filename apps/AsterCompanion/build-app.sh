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
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"
cp "$BIN_PATH/AsterCompanion" "$APP_DIR/Contents/MacOS/AsterCompanion"
cp Info.plist "$APP_DIR/Contents/Info.plist"
cp Resources/AppIcon.icns "$APP_DIR/Contents/Resources/AppIcon.icns"

# swift build already applies an ad-hoc signature to the loose binary,
# but that's from before Info.plist existed and the .app structure was
# assembled - it doesn't cover the actual bundle Launch Services and
# Keychain will see. Re-sign the complete assembled bundle as the last
# step; without this, Keychain access silently fails (no error, just an
# item that never persists) because the signature doesn't match the
# bundle identity it's being accessed under.
codesign --force --deep --sign - "$APP_DIR"

# Register the URL scheme with Launch Services so the OS routes the
# aster-companion://callback redirect back to this app.
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_DIR"

echo "Built: $APP_DIR"
