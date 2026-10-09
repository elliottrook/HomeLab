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

# Local Codex bridge: copy only the reviewed, stdlib-only modules.
# It is inert by default; review controls require explicit launch flags. Do not
# bundle worker credentials, provisioning scripts, tests or broader tools.
BRIDGE_SOURCE="$(cd ../../services/aster-agent/delegation && pwd)"
BRIDGE_DIR="$APP_DIR/Contents/Resources/LocalCodexBridge"
mkdir -p "$BRIDGE_DIR"
for module in local_bridge_cli local_turn pilot isolation_probe probe pipe_worker \
              session store contract usage transport runtime; do
    cp "$BRIDGE_SOURCE/$module.py" "$BRIDGE_DIR/$module.py"
done

# SPM builds its own resource bundle (in-app image assets declared via
# `resources:` in Package.swift) next to the loose executable, not inside
# any app structure - Bundle.module looks for it under Contents/Resources
# once running inside a real .app, so it has to be copied in explicitly.
cp -R "$BIN_PATH/AsterCompanion_AsterCompanion.bundle" "$APP_DIR/Contents/Resources/AsterCompanion_AsterCompanion.bundle"

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
if [ "${ASTER_REGISTER_APP:-1}" = "1" ]; then
    /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_DIR"
fi

echo "Built: $APP_DIR"
