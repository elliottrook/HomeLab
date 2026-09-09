#!/bin/sh
# Read-only post-update check for Aster's host GPU binding and inference path.
set -eu

die() {
    printf '%s\n' "FAIL: $*" >&2
    exit 1
}

driver=$(readlink /sys/bus/pci/devices/0000:04:00.0/driver 2>/dev/null || true)
[ "$(basename "$driver")" = "xe" ] || die "B60 04:00.0 is not bound to xe ($driver)"

qm status 105 | grep -qx 'status: stopped' || die "rollback VM 105 is not stopped"
pct status 104 | grep -qx 'status: running' || die "Aster LXC 104 is not running"
pct status 110 | grep -qx 'status: running' || die "inference LXC 110 is not running"

pct exec 104 -- systemctl is-active --quiet aster-agent.service || die "aster-agent.service is not active"
pct exec 110 -- systemctl is-active --quiet aster-llama.service || die "aster-llama.service is not active"

vulkan_summary=$(pct exec 110 -- vulkaninfo --summary 2>/dev/null) || die "vulkaninfo failed in LXC 110"
printf '%s\n' "$vulkan_summary" | grep -qi 'Intel.*BMG G21' || die "LXC 110 cannot see Intel BMG G21 through Vulkan"

printf '%s\n' 'PASS: B60 xe binding, stopped rollback VM, Aster services, and Vulkan visibility are healthy.'
