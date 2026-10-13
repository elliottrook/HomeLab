#!/bin/sh
set -eu

production=/opt/llama.cpp-b11081/llama-bench
candidate=/opt/llama.cpp-v0.6.0/llama-bench
model=/opt/models/qwen3.8-27b-iq4xs/Qwen3.8-27B-UD-IQ4_XS-00001-of-00002.gguf
result_root=/var/lib/aster-llama-experiments
run_id="$(date -u +%Y%m%dT%H%M%SZ)-llama-v060"
result_dir="$result_root/$run_id"
lock=/run/lock/aster-llama-experiment.lock

mkdir -p "$result_dir"
chmod 0700 "$result_root" "$result_dir"
exec 9>"$lock"
flock -n 9 || { echo "another inference experiment holds $lock" >&2; exit 75; }

restore() {
    systemctl start aster-llama.service || true
    systemctl is-active --quiet aster-llama.service || true
}
trap restore EXIT HUP INT TERM

date -u +%FT%TZ >"$result_dir/started-at"
uname -a >"$result_dir/uname.txt"
vulkaninfo --summary >"$result_dir/vulkan-summary.txt" 2>&1
dpkg-query -W mesa-vulkan-drivers libvulkan1 >"$result_dir/packages.txt" 2>&1
"$production" --version >"$result_dir/production-version.txt" 2>&1
"$candidate" --version >"$result_dir/candidate-version.txt" 2>&1
sha256sum "$production" "$candidate" >"$result_dir/binary-sha256.txt"
readlink -f "$model" >"$result_dir/model-target.txt"
systemctl stop aster-llama.service

run_one() {
    label=$1
    binary=$2
    kind=$3
    count=$4
    timeout 18m "$binary" -m "$model" -ngl 999 -t 4 -b 256 -ub 128 \
        -fa on -ctk q8_0 -ctv q8_0 -r 5 -o json "$kind" "$count" \
        >"$result_dir/$label-$count.json" \
        2>"$result_dir/$label-$count.stderr"
}

for label in production candidate; do
    if [ "$label" = production ]; then binary=$production; else binary=$candidate; fi
    run_one "$label" "$binary" -p 512
    run_one "$label" "$binary" -p 4096
    run_one "$label" "$binary" -n 128
done

date -u +%FT%TZ >"$result_dir/completed-at"
touch "$result_dir/COMPLETE"
trap - EXIT HUP INT TERM
systemctl start aster-llama.service
systemctl is-active --quiet aster-llama.service
