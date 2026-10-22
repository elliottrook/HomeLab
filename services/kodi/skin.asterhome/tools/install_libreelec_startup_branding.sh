#!/bin/sh
# Install the approved Aster image as both LibreELEC's and Kodi's startup splash.

set -eu

source_image=${1:-}
if [ -z "$source_image" ] || [ ! -f "$source_image" ]; then
  echo "Usage: $0 /path/to/aster-splash.png" >&2
  exit 2
fi

checkpoint_root=/storage/.aster-checkpoints
checkpoint="$checkpoint_root/aster-startup-branding-$(date +%Y%m%d-%H%M%S)"
kodi_media=/storage/.kodi/media
boot_splash=/flash/oemsplash.png

mkdir -p "$checkpoint" "$kodi_media"

for existing in "$kodi_media/splash.jpg" "$kodi_media/splash.png" "$boot_splash"; do
  if [ -f "$existing" ]; then
    cp -p "$existing" "$checkpoint/$(basename "$existing")"
  fi
done

printf '%s\n' \
  "Aster startup-branding checkpoint" \
  "Created: $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "Source SHA-256: $(sha256sum "$source_image" | cut -d' ' -f1)" \
  > "$checkpoint/manifest.txt"

# Kodi prefers splash.jpg over splash.png. Preserve it in the checkpoint, but
# refuse to shadow the approved PNG rather than deleting an unknown override.
if [ -f "$kodi_media/splash.jpg" ]; then
  echo "Refusing install: $kodi_media/splash.jpg would override splash.png." >&2
  echo "Checkpoint retained at $checkpoint" >&2
  exit 3
fi

install -m 0644 "$source_image" "$kodi_media/splash.png"

flash_writable=false
restore_flash_read_only() {
  if [ "$flash_writable" = true ]; then
    sync
    mount -o remount,ro /flash
  fi
}
trap restore_flash_read_only EXIT HUP INT TERM

mount -o remount,rw /flash
flash_writable=true
install -m 0644 "$source_image" "$boot_splash"
sync
mount -o remount,ro /flash
flash_writable=false
trap - EXIT HUP INT TERM

sha256sum "$kodi_media/splash.png" "$boot_splash"
mount | grep ' on /flash '
echo "Checkpoint: $checkpoint"
