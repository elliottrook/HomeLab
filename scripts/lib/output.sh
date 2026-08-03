#!/bin/bash

TOOLKIT_NAME="Jason's HomeLab Toolkit"
TOOLKIT_VERSION="1.0"

header() {
    local title="${1:-HomeLab Toolkit}"
    local version="development"

    if [[ -f "$HOME/lab/homelab/VERSION" ]]; then
        version="$(<"$HOME/lab/homelab/VERSION")"
    fi

    echo
    echo "══════════════════════════════════════════════"
    echo "        Jason's HomeLab Toolkit"
    printf "              Version %s\n" "$version"
    printf "              %s\n" "$title"
    echo "══════════════════════════════════════════════"
    echo
}


info() {
    echo "🔵 $1"
}

success() {
    echo "🟢 $1"
}

warning() {
    echo "🟡 $1"
}

error() {
    echo "🔴 $1" >&2
}

not_configured() {
    echo "⚪ $1"
}

disabled() {
    echo "⚫ $1"
}

divider() {
    echo
    echo "──────────────────────────────────────────────"
    echo
}

show_file_details() {
    local file="$1"

    echo "File:"
    echo "  $file"
    echo
    echo "Size:"
    du -h "$file" | awk '{print "  "$1}'
    echo
    echo "Created:"
    date "+  %A %d %B %Y %H:%M:%S"
}

footer() {
    local message="${1:-Completed}"

    divider
    success "$message"
    echo
}
