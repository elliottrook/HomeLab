#!/usr/bin/env python3
"""Build the one-file structured-emitter correction from the exact live Doctor."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


CURRENT_SHA256 = "1f7f03d1033c0696d440e1d45d3e38f3691d7446a7596c120785275cd525e587"
EXPECTED_SHA256 = "c3f4d961fe7ce2b25990c0e1317a326eeefd82a80bfc6a6e2d74461fcdfe8e09"

HELPER = r'''
# Optional, one-check machine evidence for Aster's fixed diagnostic report. The
# report builder supplies an inherited descriptor and run ID; ordinary Doctor
# runs emit nothing here and keep their existing human output unchanged.
doctor_emit_aster_state() {
    local state="${1:-}"
    local fd="${DOCTOR_STRUCTURED_FD:-}"
    local run_id="${DOCTOR_RUN_ID:-}"
    case "$state" in pass|warn|fail|unavailable) ;; *) return 2 ;; esac
    [[ "$fd" =~ ^[1-9][0-9]*$ ]] || return 0
    (( fd >= 3 )) || return 2
    [[ "$run_id" =~ ^[0-9a-f]{32}$ ]] || return 2
    [[ -e "/dev/fd/$fd" ]] || return 3
    printf '{"run_id":"%s","check_id":"aster.agent_inference","state":"%s"}\n' \
        "$run_id" "$state" >&"$fd"
}
'''

CHECK_ASTER = r'''check_aster() {
    local state

    if ! state="$(
        ssh -o BatchMode=yes -o ConnectTimeout=5 proxmox '
            agent="$(pct exec 104 -- systemctl is-active aster-agent.service 2>/dev/null || true)"
            inference="$(pct exec 110 -- systemctl is-active aster-llama.service 2>/dev/null || true)"
            api="$(pct exec 104 -- curl -sf http://192.168.70.10:9120/health 2>/dev/null || true)"
            driver="$(basename "$(readlink /sys/bus/pci/devices/0000:04:00.0/driver 2>/dev/null)" 2>/dev/null || true)"
            rollback_vm="$(qm status 105 2>/dev/null | sed -n "s/^status: //p")"
            if qm config 105 2>/dev/null | grep -Eq "^hostpci[0-9]+:.*04:00\\.0"; then
                persistent_b60=yes
            else
                persistent_b60=no
            fi
            printf "agent=%s\\ninference=%s\\napi=%s\\ndriver=%s\\nrollback_vm=%s\\npersistent_b60=%s\\n" "$agent" "$inference" "$api" "$driver" "$rollback_vm" "$persistent_b60"
        '
    )"; then
        doctor_emit_aster_state unavailable
        warn "Unable to check Aster services"
        return
    fi

    if grep -qx 'agent=active' <<< "$state" &&
       grep -qx 'inference=active' <<< "$state" &&
       grep -q '"status":"ok"' <<< "$state" &&
       grep -qx 'driver=xe' <<< "$state" &&
       grep -qx 'rollback_vm=stopped' <<< "$state" &&
       grep -qx 'persistent_b60=no' <<< "$state"; then
        doctor_emit_aster_state pass
        pass "Aster agent API healthy; llama.cpp service active; B60 xe bound; GPU offload not verified"
    else
        doctor_emit_aster_state fail
        fail "Aster service unhealthy: $(tr '\n' ' ' <<< "$state" | sed 's/[[:space:]]*$//')"
    fi
}
'''


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"{label} anchor count is {text.count(old)}, expected 1")
    return text.replace(old, new, 1)


def patch_text(text: str) -> str:
    text = replace_once(
        text,
        'source "$REPO/scripts/lib/output.sh"\n',
        'source "$REPO/scripts/lib/output.sh"\n' + HELPER,
        "helper",
    )
    marker = "\ncheck_aster() {\n"
    marker_start = text.find(marker)
    start = marker_start + 1 if marker_start >= 0 else -1
    boundary = "\n}\n\ncheck_aster_lab_operations() {"
    end = text.find(boundary, start)
    if start < 0 or end < 0 or text.find(marker, start + len(marker)) >= 0:
        raise ValueError("check_aster boundary is not unique")
    text = text[:start] + CHECK_ASTER + "\ncheck_aster_lab_operations() {" + text[end + len(boundary):]
    return text


def build(source: Path, destination: Path) -> str:
    raw = source.read_bytes()
    if sha256(raw) != CURRENT_SHA256:
        raise ValueError("live Doctor predecessor hash mismatch")
    patched = patch_text(raw.decode("utf-8")).encode("utf-8")
    observed = sha256(patched)
    if EXPECTED_SHA256 != "TO_BE_FROZEN" and observed != EXPECTED_SHA256:
        raise ValueError("generated Doctor hash mismatch")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(destination, flags, 0o700)
    with os.fdopen(fd, "wb") as stream:
        stream.write(patched)
    return observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(build(args.source, args.destination))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
