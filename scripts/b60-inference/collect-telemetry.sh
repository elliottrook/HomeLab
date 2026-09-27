#!/bin/sh
# Run inside LXC 110. Read-only and secret-free; emits a strict key=value snapshot.
set -eu

pid="$(systemctl show aster-llama.service -p MainPID --value)"
case "$pid" in *[!0-9]*|'') exit 2 ;; esac
hwmon="$(find -L /sys/class/drm/card*/device/hwmon -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -n 1)"

temperature() {
    label="$1"
    for input in "$hwmon"/temp*_input; do
        base="${input%_input}"
        if [ "$(cat "${base}_label" 2>/dev/null || true)" = "$label" ]; then
            cat "$input"
            return
        fi
    done
    printf '0\n'
}

drm_max_kib() {
    metric="$1"
    awk -v key="$metric" '$1 == key ":" { if (($2 + 0) > max) max = $2 + 0 } END { print max + 0 }' \
        /proc/"$pid"/fdinfo/* 2>/dev/null
}

mem_total="$(awk '$1 == "MemTotal:" {print $2}' /proc/meminfo)"
mem_available="$(awk '$1 == "MemAvailable:" {print $2}' /proc/meminfo)"
affinity="$(taskset -pc "$pid" | sed 's/.*: //')"

printf 'schema_version=1.0.0\n'
printf 'recorded_at=%s\n' "$(date --iso-8601=seconds)"
printf 'source_pid=%s\n' "$pid"
printf 'gpu_driver=xe\n'
printf 'gpu_temp_pkg_millic=%s\n' "$(temperature pkg)"
printf 'gpu_temp_vram_millic=%s\n' "$(temperature vram)"
printf 'vram_resident_kib=%s\n' "$(drm_max_kib drm-resident-vram0)"
printf 'gtt_resident_kib=%s\n' "$(drm_max_kib drm-resident-gtt)"
printf 'ram_total_kib=%s\n' "$mem_total"
printf 'ram_available_kib=%s\n' "$mem_available"
printf 'cpu_affinity=%s\n' "$affinity"
printf 'gpu_frequency_mhz=unavailable\n'
printf 'gpu_power_w=unavailable\n'
