#!/bin/sh
# Read-only post-update check for Aster's accepted SYCL inference path.
set -eu

die() {
    printf '%s\n' "FAIL: $*" >&2
    exit 1
}

driver=$(readlink /sys/bus/pci/devices/0000:04:00.0/driver 2>/dev/null || true)
[ "$(basename "$driver")" = "xe" ] || die "B60 04:00.0 is not bound to xe ($driver)"

qm status 105 | grep -qx 'status: stopped' || die "rollback VM 105 is not stopped"
if qm config 105 | grep -Eq '^hostpci[0-9]+:.*04:00\.0'; then
    die "rollback VM 105 persistently maps B60 04:00.0"
fi
pct status 104 | grep -qx 'status: running' || die "Aster LXC 104 is not running"
pct status 110 | grep -qx 'status: running' || die "inference LXC 110 is not running"

pct exec 104 -- systemctl is-active --quiet aster-agent.service || die "aster-agent.service is not active"
pct exec 110 -- systemctl is-active --quiet aster-llama.service || die "aster-llama.service is not active"

device=$(pct exec 110 -- stat -c '%t:%T:%G' /dev/dri/renderD128 2>/dev/null) || \
    die "LXC 110 cannot see renderD128"
[ "$device" = 'e2:80:render' ] || die "LXC 110 renderD128 custody is unexpected ($device)"

unit=$(pct exec 110 -- systemctl show aster-llama.service \
    -p Environment -p ExecStart -p ActiveState -p SubState -p NRestarts \
    --no-pager 2>/dev/null) || die "cannot inspect aster-llama.service"
printf '%s\n' "$unit" | grep -Fxq 'ActiveState=active' || die "aster-llama is not active"
printf '%s\n' "$unit" | grep -Fxq 'SubState=running' || die "aster-llama is not running"
printf '%s\n' "$unit" | grep -Fxq 'NRestarts=0' || die "aster-llama has restarted"
printf '%s\n' "$unit" | grep -Fq 'ONEAPI_DEVICE_SELECTOR=level_zero:gpu' || \
    die "aster-llama is not pinned to Level Zero"
printf '%s\n' "$unit" | grep -Fq \
    '/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server' || \
    die "aster-llama is not using the accepted SYCL binary"
printf '%s\n' "$unit" | grep -Fq \
    '/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf' || \
    die "aster-llama is not using the accepted model"
printf '%s\n' "$unit" | grep -Fq -- '--api-key-file /etc/aster-llama-api-keys' || \
    die "aster-llama authentication boundary is missing"

inference_health=$(pct exec 110 -- curl --fail --silent --show-error --max-time 5 \
    http://192.168.70.12:11435/health 2>/dev/null) || die "inference health endpoint is unavailable"
printf '%s\n' "$inference_health" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' || \
    die "inference health endpoint did not report ok"

printf '%s\n' 'PASS: B60 xe binding, stopped rollback VM, Aster services, accepted SYCL/Level Zero identity, and inference health.'
