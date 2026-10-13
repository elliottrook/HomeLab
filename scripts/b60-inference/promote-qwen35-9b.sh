#!/bin/sh
set -eu

guest=110
news_guest=114
endpoint=http://192.168.70.12:11435
unit=/etc/systemd/system/aster-llama.service
rollback=/etc/systemd/system/aster-llama.service.pre-9b-20261010
candidate=/tmp/aster-llama-9b.service
staging=/dev/shm/b60-qwen35-9b
model_source=$staging/model/Qwen3.5-9B-Q4_K_M.gguf
archive=$staging/runtime/llama-b11429.tar.gz
runtime_source=$staging/runtime/llama-b11429
runtime_target=/opt/llama.cpp-b11429
model_target=/usr/share/ollama/.ollama/models/blobs/sha256-cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13
model_link=/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf
legacy_manifest=/usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/qwen3.5/9b
legacy_blob=/usr/share/ollama/.ollama/models/blobs/sha256-dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c
accepted_binary_sha=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
accepted_unit_sha=e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184
rollback_q8_sha=7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013
model_sha=cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13
archive_sha=632c4e98feba2b94407a2130e3133e0c3aefb0ea1ab41337e926d8bfafdd0b74
legacy_sha=dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c
candidate_sha=6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e
armed=0

wait_for_health() {
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        if pct exec "$guest" -- systemctl is-active --quiet aster-llama.service &&
           pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null; then return 0; fi
        attempt=$((attempt + 1)); sleep 5
    done
    return 1
}

restore_timers() {
    pct exec "$news_guest" -- systemctl start news-aggregator-ingest.timer
    pct exec "$news_guest" -- systemctl start news-aggregator-digest.timer
}

rollback_production() {
    status=$?
    trap - EXIT HUP INT TERM
    if [ "$armed" -eq 1 ]; then
        pct exec "$guest" -- install -o root -g root -m 0644 "$rollback" "$unit" || true
        pct exec "$guest" -- systemctl daemon-reload || true
        pct exec "$guest" -- systemctl stop aster-llama.service || true
        sleep 30
        pct exec "$guest" -- systemctl start --no-block aster-llama.service || true
        wait_for_health || status=1
    fi
    restore_timers || status=1
    exit "$status"
}

test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$accepted_binary_sha"
test "$(pct exec "$guest" -- sha256sum "$unit" | awk '{print $1}')" = "$accepted_unit_sha"
test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service.pre-q4-20261010 | awk '{print $1}')" = "$rollback_q8_sha"
test "$(pct exec "$guest" -- sha256sum "$model_source" | awk '{print $1}')" = "$model_sha"
test "$(pct exec "$guest" -- sha256sum "$archive" | awk '{print $1}')" = "$archive_sha"
test "$(pct exec "$guest" -- sha256sum "$legacy_blob" | awk '{print $1}')" = "$legacy_sha"
test "$(pct exec "$guest" -- sha256sum "$candidate" | awk '{print $1}')" = "$candidate_sha"
test "$(pct exec "$guest" -- grep -rl "$legacy_sha" /usr/share/ollama/.ollama/models/manifests | wc -l)" -eq 1
test "$(pct exec "$guest" -- grep -l "$legacy_sha" "$legacy_manifest")" = "$legacy_manifest"
pct exec "$guest" -- test ! -e "$rollback"
pct exec "$guest" -- test ! -e "$runtime_target"
pct exec "$guest" -- test ! -e "$model_target"
pct exec "$guest" -- systemctl is-active --quiet aster-llama.service
pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null

pct exec "$news_guest" -- systemctl stop news-aggregator-ingest.timer
pct exec "$news_guest" -- systemctl stop news-aggregator-digest.timer
trap rollback_production EXIT HUP INT TERM
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-ingest.service && exit 1 || true
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-digest.service && exit 1 || true
pct exec "$guest" -- install -o root -g root -m 0644 "$unit" "$rollback"
armed=1
pct exec "$guest" -- systemctl stop aster-llama.service
sleep 30
pct exec "$guest" -- awk '/MemAvailable/ {if ($2 < 4194304) exit 1}' /proc/meminfo

pct exec "$guest" -- tar -xzf "$archive" -C "$staging/runtime"
pct exec "$guest" -- test -x "$runtime_source/llama-server"
pct exec "$guest" -- rm -f -- "$legacy_manifest" "$legacy_blob"
pct exec "$guest" -- cp -a "$runtime_source" "$runtime_target.installing"
pct exec "$guest" -- mv "$runtime_target.installing" "$runtime_target"
pct exec "$guest" -- install -o ollama -g ollama -m 0644 "$model_source" "$model_target.installing"
pct exec "$guest" -- mv "$model_target.installing" "$model_target"
pct exec "$guest" -- mkdir -p /opt/models/qwen3.5-9b-q4km
pct exec "$guest" -- ln -s "$model_target" "$model_link"
pct exec "$guest" -- install -o root -g root -m 0644 "$candidate" "$unit"
pct exec "$guest" -- systemctl daemon-reload
pct exec "$guest" -- systemctl start --no-block aster-llama.service
wait_for_health

test "$(pct exec "$guest" -- sha256sum "$unit" | awk '{print $1}')" = "$candidate_sha"
test "$(pct exec "$guest" -- sha256sum "$runtime_target/llama-server" | awk '{print $1}')" != "$accepted_binary_sha"
test "$(pct exec "$guest" -- sha256sum "$model_target" | awk '{print $1}')" = "$model_sha"
pct exec "$guest" -- sh -c 'vulkaninfo --summary 2>/dev/null | grep -q "BMG G21"'
test "$(lspci -nnk -s 04:00.0 | awk -F': ' '/Kernel driver in use/ {print $2}')" = xe
pct exec "$guest" -- awk '/MemAvailable/ {if ($2 < 4194304) exit 1}' /proc/meminfo
test "$(pct exec "$guest" -- df -B1 --output=avail / | tail -1)" -ge 21474836480

restore_timers
trap - EXIT HUP INT TERM
