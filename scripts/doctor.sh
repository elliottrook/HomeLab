#!/bin/bash

set -u

REPO="$HOME/lab/homelab"
SERVICES_CONFIG="$REPO/configs/services.conf"
BACKUP_ROOT="$HOME/lab/private-backups"

source "$REPO/scripts/lib/output.sh"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
    success "$1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

warn() {
    warning "$1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
    error "$1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_tcp() {
    local display="$1"
    local ip="$2"
    local port="$3"

    if nc -z -G 3 "$ip" "$port" >/dev/null 2>&1; then
        pass "$display — $ip:$port"
    else
        fail "$display — $ip:$port"
    fi
}

check_backup_age() {
    local display="$1"
    local directory="$2"
    local maximum_hours="${3:-48}"

    if [[ ! -d "$directory" ]]; then
        warn "$display backup directory does not exist"
        return
    fi

    local latest
    latest="$(
        find "$directory" -type f ! -name '*.sha256' -print0 2>/dev/null |
        xargs -0 stat -f '%m %N' 2>/dev/null |
        sort -nr |
        head -n 1
    )"

    if [[ -z "$latest" ]]; then
        warn "$display has no backup files"
        return
    fi

    local modified_epoch
    modified_epoch="${latest%% *}"

    local now_epoch
    now_epoch="$(date +%s)"

    local age_hours
    age_hours=$(( (now_epoch - modified_epoch) / 3600 ))

    if (( age_hours <= maximum_hours )); then
        pass "$display backup is ${age_hours} hour(s) old"
    else
        warn "$display backup is ${age_hours} hour(s) old"
    fi
}

check_pihole_dns() {
    local display="$1"
    local ip="$2"
    local public_answer
    local local_answer
    local blocked_answer

    public_answer="$(dig +time=3 +tries=1 +short @"$ip" example.com A 2>/dev/null)"
    local_answer="$(dig +time=3 +tries=1 +short @"$ip" home.internal A 2>/dev/null)"
    blocked_answer="$(dig +time=3 +tries=1 +short @"$ip" doubleclick.net A 2>/dev/null)"

    if [[ -z "$public_answer" ]]; then
        fail "$display did not resolve a public domain"
    elif ! grep -qx '192\.168\.1\.20' <<< "$local_answer"; then
        fail "$display did not resolve home.internal correctly"
    elif [[ -n "$blocked_answer" ]] && ! grep -Eqx '0\.0\.0\.0|::' <<< "$blocked_answer"; then
        fail "$display did not block the test domain"
    else
        pass "$display resolves public/local DNS and blocks the test domain"
    fi
}

header "HomeLab Doctor"

info "Checking internet connectivity..."

if nc -z -G 5 1.1.1.1 443 >/dev/null 2>&1; then
    pass "Internet connectivity"
else
    fail "Internet connectivity"
fi

divider

info "Checking DNS resolution..."

if dscacheutil -q host -a name github.com 2>/dev/null | grep -q 'ip_address'; then
    pass "DNS resolution"
else
    fail "DNS resolution"
fi

check_pihole_dns "Pi-hole Primary" "192.168.1.20"
check_pihole_dns "Pi-hole Secondary" "192.168.1.40"

divider

info "Checking configured services..."

if [[ -f "$SERVICES_CONFIG" ]]; then
    while IFS='|' read -r name display ip port; do
        [[ -z "$name" || "$name" == \#* ]] && continue
        check_tcp "$display" "$ip" "$port"
    done < "$SERVICES_CONFIG"
else
    warn "Service configuration not found"
fi

divider

info "Checking configuration backups..."

check_backup_age "OPNsense" "$BACKUP_ROOT/opnsense" 48
check_backup_age "Arista" "$BACKUP_ROOT/arista" 48
check_backup_age "Proxmox" "$BACKUP_ROOT/proxmox" 48

divider

info "Checking Mac disk usage..."

DISK_PERCENT="$(
    df -Pk "$HOME" |
    awk 'NR == 2 {gsub("%", "", $5); print $5}'
)"

if [[ -z "$DISK_PERCENT" ]]; then
    warn "Unable to determine disk usage"
elif (( DISK_PERCENT < 80 )); then
    pass "Mac disk usage is ${DISK_PERCENT}%"
elif (( DISK_PERCENT < 90 )); then
    warn "Mac disk usage is ${DISK_PERCENT}%"
else
    fail "Mac disk usage is ${DISK_PERCENT}%"
fi

divider

info "Checking Git repository..."

if [[ ! -d "$REPO/.git" ]]; then
    fail "HomeLab Git repository not found"
else
    GIT_STATUS="$(git -C "$REPO" status --porcelain 2>/dev/null)"

    if [[ -z "$GIT_STATUS" ]]; then
        pass "Git working tree is clean"
    else
        warn "Git repository contains uncommitted changes"
    fi

    if git -C "$REPO" remote get-url origin >/dev/null 2>&1; then
        pass "Git remote is configured"
    else
        warn "Git remote is not configured"
    fi
fi

divider

echo "Summary"
echo
echo "🟢 Passed:   $PASS_COUNT"
echo "🟡 Warnings: $WARN_COUNT"
echo "🔴 Failed:   $FAIL_COUNT"
echo

if (( FAIL_COUNT > 0 )); then
    error "HomeLab doctor found one or more failures"
    exit 1
elif (( WARN_COUNT > 0 )); then
    warning "HomeLab is operational with warnings"
    exit 0
else
    success "HomeLab is healthy"
    exit 0
fi
