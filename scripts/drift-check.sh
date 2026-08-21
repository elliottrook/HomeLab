#!/bin/bash

set -euo pipefail
umask 077

REPO="$HOME/lab/homelab"
BACKUP_ROOT="$HOME/lab/private-backups"
STATE_DIR="${HOMELAB_STATE_ROOT:-$HOME/lab/monitoring-state}/drift"
BASELINE="$STATE_DIR/baseline.manifest"
BASELINE_INFO="$STATE_DIR/baseline.info"
LAST_ALERT="$STATE_DIR/last-alert.sha256"
ALERT_SCRIPT="$REPO/scripts/backup-alert"

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

latest_file() {
    find "$1" -maxdepth 1 -type f -name "$2" -print |
        sort |
        tail -1
}

latest_directory() {
    find "$1" -mindepth 1 -maxdepth 1 -type d -print |
        sort |
        tail -1
}

require_file() {
    if [[ ! -f "$1" ]]; then
        printf 'ERROR: Required file not found: %s\n' "$1" >&2
        exit 2
    fi
}

require_directory() {
    if [[ ! -d "$1" ]]; then
        printf 'ERROR: Required directory not found: %s\n' "$1" >&2
        exit 2
    fi
}

build_opnsense_manifest() {
    local source_file="$1"
    local output_file="$2"

    python3 - "$source_file" >> "$output_file" <<'PYTHON'
import copy
import hashlib
import sys
import xml.etree.ElementTree as ET

source = sys.argv[1]
root = ET.parse(source).getroot()

def sanitize(element):
    element.attrib.pop("persisted_at", None)

    if element.text is not None and not element.text.strip():
        element.text = None

    if element.tail is not None and not element.tail.strip():
        element.tail = None

    for child in list(element):
        if child.tag == "revision":
            element.remove(child)
        else:
            sanitize(child)

def digest(element):
    candidate = copy.deepcopy(element)
    sanitize(candidate)
    payload = ET.tostring(
        candidate,
        encoding="utf-8",
        short_empty_elements=True,
    )
    return hashlib.sha256(payload).hexdigest()

sanitize(root)
print(f"opnsense:configuration\t{digest(root)}")

counts = {}
for child in list(root):
    counts[child.tag] = counts.get(child.tag, 0) + 1
    suffix = f"[{counts[child.tag]}]" if counts[child.tag] > 1 else ""
    print(f"opnsense:{child.tag}{suffix}\t{digest(child)}")

    if child.tag == "OPNsense":
        nested_counts = {}
        for nested in list(child):
            nested_counts[nested.tag] = nested_counts.get(nested.tag, 0) + 1
            nested_suffix = (
                f"[{nested_counts[nested.tag]}]"
                if nested_counts[nested.tag] > 1
                else ""
            )
            print(
                f"opnsense:OPNsense/{nested.tag}{nested_suffix}"
                f"\t{digest(nested)}"
            )
PYTHON
}

build_arista_manifest() {
    local backup_dir="$1"
    local output_file="$2"
    local filename
    local checksum

    for filename in \
        running-config.txt \
        startup-config.txt
    do
        require_file "$backup_dir/$filename"
        checksum="$(
            shasum -a 256 "$backup_dir/$filename" |
            awk '{print $1}'
        )"
        printf 'arista:%s\t%s\n' "$filename" "$checksum" >> "$output_file"
    done
}

is_protected_proxmox_path() {
    case "$1" in
        etc/network/interfaces|\
        etc/hosts|\
        etc/hostname|\
        etc/resolv.conf|\
        etc/pve/storage.cfg|\
        etc/pve/user.cfg|\
        etc/pve/datacenter.cfg|\
        etc/pve/replication.cfg|\
        etc/pve/vzdump.cron|\
        etc/pve/jobs.cfg|\
        etc/pve/firewall/*.fw|\
        etc/pve/sdn/*.cfg|\
        etc/pve/sdn/*/*.cfg|\
        etc/pve/mapping/*.cfg|\
        etc/pve/ha/*.cfg|\
        etc/pve/nodes/*/lxc/*.conf|\
        etc/pve/nodes/*/qemu-server/*.conf)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

build_proxmox_manifest() {
    local archive="$1"
    local output_file="$2"
    local archive_path
    local checksum
    local protected_count=0

    while IFS= read -r archive_path; do
        [[ "$archive_path" == */ ]] && continue

        if is_protected_proxmox_path "$archive_path"; then
            checksum="$(
                tar -xOzf "$archive" "$archive_path" |
                shasum -a 256 |
                awk '{print $1}'
            )"

            printf 'proxmox:%s\t%s\n' \
                "$archive_path" \
                "$checksum" >> "$output_file"

            protected_count=$((protected_count + 1))
        fi
    done < <(tar -tzf "$archive")

    if [[ "$protected_count" -eq 0 ]]; then
        printf 'ERROR: No protected Proxmox files found in %s\n' \
            "$archive" >&2
        exit 2
    fi
}

build_manifest() {
    local output_file="$1"
    local unsorted_file="$output_file.unsorted"
    local opnsense_file
    local arista_dir
    local proxmox_dir
    local proxmox_archive

    opnsense_file="$(
        latest_file "$BACKUP_ROOT/opnsense" '*.xml'
    )"
    arista_dir="$(
        latest_directory "$BACKUP_ROOT/arista"
    )"
    proxmox_dir="$(
        latest_directory "$BACKUP_ROOT/proxmox"
    )"
    proxmox_archive="$proxmox_dir/proxmox-host-config.tar.gz"

    require_file "$opnsense_file"
    require_directory "$arista_dir"
    require_file "$proxmox_archive"

    : > "$unsorted_file"

    build_opnsense_manifest "$opnsense_file" "$unsorted_file"
    build_arista_manifest "$arista_dir" "$unsorted_file"
    build_proxmox_manifest "$proxmox_archive" "$unsorted_file"

    sort -u "$unsorted_file" > "$output_file"
    rm -f "$unsorted_file"

    chmod 600 "$output_file"

    CURRENT_OPNSENSE="$opnsense_file"
    CURRENT_ARISTA="$arista_dir"
    CURRENT_PROXMOX="$proxmox_dir"
}

describe_changes() {
    local old_manifest="$1"
    local new_manifest="$2"

    awk -F '\t' '
        NR == FNR {
            old[$1] = $2
            next
        }

        {
            new[$1] = $2
        }

        END {
            for (key in old) {
                if (!(key in new)) {
                    print "REMOVED: " key
                } else if (old[key] != new[key]) {
                    print "CHANGED: " key
                }
            }

            for (key in new) {
                if (!(key in old)) {
                    print "ADDED: " key
                }
            }
        }
    ' "$old_manifest" "$new_manifest" |
        sort
}

accept_baseline() {
    current=""
    current="$(mktemp "$STATE_DIR/current.XXXXXX")"
    trap 'rm -f "$current"' EXIT

    build_manifest "$current"
    mv -f "$current" "$BASELINE"

    {
        printf 'accepted_at=%s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
        printf 'opnsense_source=%s\n' "$CURRENT_OPNSENSE"
        printf 'arista_source=%s\n' "$CURRENT_ARISTA"
        printf 'proxmox_source=%s\n' "$CURRENT_PROXMOX"
    } > "$BASELINE_INFO"

    chmod 600 "$BASELINE" "$BASELINE_INFO"
    rm -f "$LAST_ALERT"

    trap - EXIT

    printf 'Configuration drift baseline accepted.\n'
    printf 'Protected entries: %s\n' "$(wc -l < "$BASELINE" | tr -d ' ')"
    cat "$BASELINE_INFO"
}

check_drift() {
    current=""
    changes=""
    local signature
    local previous_signature=""
    local message

    if [[ ! -f "$BASELINE" ]]; then
        printf 'No accepted drift baseline exists.\n' >&2
        printf 'Review current health, then run:\n' >&2
        printf '  %s accept\n' "$0" >&2
        exit 2
    fi

    current="$(mktemp "$STATE_DIR/current.XXXXXX")"
    changes="$(mktemp "$STATE_DIR/changes.XXXXXX")"
    trap 'rm -f "$current" "$changes"' EXIT

    build_manifest "$current"
    describe_changes "$BASELINE" "$current" > "$changes"

    if [[ ! -s "$changes" ]]; then
        rm -f "$LAST_ALERT"
        printf 'Configuration drift: NONE\n'
        printf 'Baseline: %s\n' \
            "$(awk -F= '$1 == "accepted_at" {print $2}' "$BASELINE_INFO")"
        printf 'Protected entries: %s\n' \
            "$(wc -l < "$current" | tr -d ' ')"
        return 0
    fi

    printf 'Configuration drift: DETECTED\n'
    cat "$changes"

    signature="$(
        cat "$BASELINE" "$current" |
        shasum -a 256 |
        awk '{print $1}'
    )"

    if [[ -f "$LAST_ALERT" ]]; then
        previous_signature="$(cat "$LAST_ALERT")"
    fi

    if [[ "$signature" != "$previous_signature" ]]; then
        message="$(
            printf '%s\n\n' \
                'Protected HomeLab configuration changed relative to the accepted baseline.'
            cat "$changes"
            printf '\nReview the newest infrastructure backups.\n'
            printf 'If the changes are intentional, run:\n'
            printf '  lab drift accept\n'
        )"

        if "$ALERT_SCRIPT" \
            "Mini Atlas configuration drift detected" \
            "$message"
        then
            printf '%s\n' "$signature" > "$LAST_ALERT"
            chmod 600 "$LAST_ALERT"
            printf 'A drift notification was sent.\n'
        else
            printf 'WARNING: The drift notification could not be sent.\n' >&2
        fi
    else
        printf 'This drift condition was already reported; email suppressed.\n'
    fi

    exit 1
}

show_status() {
    if [[ ! -f "$BASELINE" ]]; then
        printf 'Configuration drift baseline: NOT CONFIGURED\n'
        exit 1
    fi

    printf 'Configuration drift baseline:\n'
    cat "$BASELINE_INFO"
    printf 'protected_entries=%s\n' \
        "$(wc -l < "$BASELINE" | tr -d ' ')"

    if [[ -f "$LAST_ALERT" ]]; then
        printf 'unresolved_alert=yes\n'
    else
        printf 'unresolved_alert=no\n'
    fi
}

case "${1:-check}" in
    check)
        check_drift
        ;;
    accept)
        accept_baseline
        ;;
    status)
        show_status
        ;;
    *)
        printf 'Usage: %s {check|accept|status}\n' "$0" >&2
        exit 2
        ;;
esac
