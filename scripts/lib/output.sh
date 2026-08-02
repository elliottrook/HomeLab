#!/bin/bash

# Terminal colours
RESET='\033[0m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'

info() {
    printf "${BLUE}ℹ %s${RESET}\n" "$1"
}

success() {
    printf "${GREEN}✓ %s${RESET}\n" "$1"
}

warning() {
    printf "${YELLOW}⚠ %s${RESET}\n" "$1"
}

error() {
    printf "${RED}✗ %s${RESET}\n" "$1" >&2
}

heading() {
    echo
    echo "=========================================="
    echo "$1"
    echo "=========================================="
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
